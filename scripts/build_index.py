#!/usr/bin/env python3
# scripts/build_index.py
#
# Academy KB indexer with metrics:
# - Splits long docs into chunks for embeddings
# - Parses YAML front matter to metadata
# - Normalizes metadata to Chroma-safe scalars
# - Retries on 429 rate limits
# - Logs per-document stats to SQLite: data/telemetry.db
# - Supports: .md .txt .html .pdf .docx .csv

import os, re, time, json, glob, hashlib, csv, sys, sqlite3
from datetime import datetime, UTC
from typing import List, Dict, Tuple
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ---------------- Config (env-overridable) ----------------
RAW_ROOT       = os.getenv("RAW_ROOT", "data/raw")
CHROMA_DIR     = os.getenv("CHROMA_DIR", "data/chroma")
COLLECTION     = os.getenv("CHROMA_COLLECTION", "academy_kb")
EMBED_MODEL    = os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-small")
CHUNK_TOKENS   = int(os.getenv("CHUNK_TOKENS", "1000"))
CHUNK_OVERLAP  = int(os.getenv("CHUNK_OVERLAP", "100"))
BATCH_SIZE     = int(os.getenv("EMBED_BATCH_SIZE", "64"))
EMBED_RETRIES  = int(os.getenv("EMBED_RETRIES", "5"))
EMBED_BACKOFF  = float(os.getenv("EMBED_BACKOFF", "1.0"))  # seconds base

# metrics DB
METRICS_DB     = os.getenv("METRICS_DB", "data/telemetry.db")

# ---------------- Third-party libs ----------------
import chromadb
from chromadb.config import Settings
from pypdf import PdfReader
from docx import Document as DocxDocument
try:
    from markdownify import markdownify as html_to_md
except Exception:
    html_to_md = None

import tiktoken
from openai import OpenAI

# ---------------- Utilities ----------------
FRONT_MATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n?", re.DOTALL)

def now_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")

def ensure_metrics_db():
    os.makedirs(os.path.dirname(METRICS_DB), exist_ok=True)
    con = sqlite3.connect(METRICS_DB)
    cur = con.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS documents (
      doc_id TEXT PRIMARY KEY,
      title TEXT,
      path TEXT,
      source TEXT,
      tags TEXT,
      categories TEXT,
      url TEXT,
      video_url TEXT,
      last_updated TEXT,
      chars INTEGER,
      tokens INTEGER,
      chunk_count INTEGER,
      last_indexed TEXT
    )
    """)
    con.commit()
    con.close()

def upsert_document_row(row: Dict):
    con = sqlite3.connect(METRICS_DB)
    cur = con.cursor()
    cur.execute("""
    INSERT INTO documents
      (doc_id, title, path, source, tags, categories, url, video_url, last_updated, chars, tokens, chunk_count, last_indexed)
    VALUES
      (:doc_id, :title, :path, :source, :tags, :categories, :url, :video_url, :last_updated, :chars, :tokens, :chunk_count, :last_indexed)
    ON CONFLICT(doc_id) DO UPDATE SET
      title=excluded.title,
      path=excluded.path,
      source=excluded.source,
      tags=excluded.tags,
      categories=excluded.categories,
      url=excluded.url,
      video_url=excluded.video_url,
      last_updated=excluded.last_updated,
      chars=excluded.chars,
      tokens=excluded.tokens,
      chunk_count=excluded.chunk_count,
      last_indexed=excluded.last_indexed
    """, row)
    con.commit()
    con.close()

def parse_front_matter(text: str) -> Tuple[Dict, str]:
    """Return (meta, body) with permissive YAML (key: value, [a, b])."""
    m = FRONT_MATTER_RE.match(text)
    meta: Dict = {}
    if m:
        raw = m.group(1)
        for line in raw.splitlines():
            s = line.strip()
            if not s or s.startswith("#") or ":" not in s:
                continue
            k, v = s.split(":", 1)
            key = k.strip()
            val = v.strip()
            if (val.startswith("'") and val.endswith("'")) or (val.startswith('"') and val.endswith('"')):
                val = val[1:-1]
            if val.startswith("[") and val.endswith("]"):
                inner = val[1:-1].strip()
                meta[key] = [x.strip().strip("'").strip('"') for x in inner.split(",")] if inner else []
            else:
                meta[key] = val
        return meta, text[m.end():]
    return {}, text

def normalize_scalar(v):
    """Chroma requires scalar metadata; we also store scalars in SQLite."""
    if v is None or isinstance(v, (str, int, float, bool)):
        return v
    if isinstance(v, (list, tuple, set)):
        return ", ".join(str(x) for x in v)
    try:
        return json.dumps(v, ensure_ascii=False)
    except Exception:
        return str(v)

def normalize_metadata(meta: Dict) -> Dict:
    return {k: normalize_scalar(v) for k, v in meta.items()}

def read_txt(path: str) -> str:
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()

def read_pdf(path: str) -> str:
    reader = PdfReader(path)
    out = []
    for p in reader.pages:
        try:
            out.append(p.extract_text() or "")
        except Exception:
            pass
    return "\n".join(out).strip()

def read_docx(path: str) -> str:
    doc = DocxDocument(path)
    return "\n".join(p.text for p in doc.paragraphs)

def read_html(path: str) -> str:
    raw = read_txt(path)
    if html_to_md:
        try:
            return html_to_md(raw)
        except Exception:
            pass
    return re.sub(r"<[^>]+>", "", raw)

def read_csv_text(path: str) -> str:
    rows = []
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        r = csv.DictReader(f)
        rows.extend(r)
    return json.dumps(rows, ensure_ascii=False, indent=2)

READERS = {
    ".md":   read_txt,
    ".txt":  read_txt,
    ".html": read_html,
    ".htm":  read_html,
    ".pdf":  read_pdf,
    ".docx": read_docx,
    ".csv":  read_csv_text,
}

def file_id(path: str) -> str:
    return hashlib.sha1(path.encode("utf-8")).hexdigest()

def title_from_meta_or_path(meta: Dict, path: str) -> str:
    if str(meta.get("title", "")).strip():
        return str(meta["title"]).strip()
    return os.path.splitext(os.path.basename(path))[0].replace("-", " ").strip()

def gather_files(root: str) -> List[str]:
    paths: List[str] = []
    for ext in READERS.keys():
        paths += glob.glob(os.path.join(root, "**", f"*{ext}"), recursive=True)
    return sorted(paths)

def read_file_text(path: str) -> Tuple[Dict, str]:
    ext = os.path.splitext(path)[1].lower()
    reader = READERS.get(ext)
    if not reader:
        return {}, ""
    text = reader(path)
    if ext in (".md", ".txt"):
        meta, body = parse_front_matter(text)
        return meta, body
    return {}, text

# ---------------- Chunking ----------------
def get_encoder():
    return tiktoken.get_encoding("cl100k_base")

ENC = None
def tokenize(text: str) -> List[int]:
    global ENC
    if ENC is None:
        ENC = get_encoder()
    return ENC.encode(text)

def detokenize(tokens: List[int]) -> str:
    return ENC.decode(tokens)

def chunk_text(text: str, chunk_tokens: int, overlap_tokens: int) -> List[str]:
    toks = tokenize(text)
    n = len(toks)
    if n == 0:
        return []
    chunks: List[str] = []
    start = 0
    while start < n:
        end = min(start + chunk_tokens, n)
        chunks.append(detokenize(toks[start:end]))
        if end == n:
            break
        start = max(0, end - overlap_tokens)
    return chunks

def make_chunk_id(doc_id: str, idx: int) -> str:
    return f"{doc_id}_{idx:05d}"

# ---------------- OpenAI embeddings (retry) ----------------
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def embed_batch(texts: List[str]) -> List[List[float]]:
    delay = EMBED_BACKOFF
    for attempt in range(1, EMBED_RETRIES + 1):
        try:
            resp = client.embeddings.create(model=EMBED_MODEL, input=texts)
            return [d.embedding for d in resp.data]
        except Exception as e:
            msg = str(e).lower()
            transient = ("429" in msg) or ("rate limit" in msg) or ("temporar" in msg)
            if transient and attempt < EMBED_RETRIES:
                time.sleep(delay)
                delay *= 2
                continue
            raise

def embed_all(texts: List[str], batch_size: int = BATCH_SIZE) -> List[List[float]]:
    out: List[List[float]] = []
    for i in range(0, len(texts), batch_size):
        vecs = embed_batch(texts[i:i + batch_size])
        out.extend(vecs)
        time.sleep(0.05)
    return out

# ---------------- Chroma helpers ----------------
def get_collection():
    client = chromadb.PersistentClient(path=CHROMA_DIR, settings=Settings(allow_reset=True))
    try:
        return client.get_collection(COLLECTION)
    except Exception:
        return client.create_collection(COLLECTION)

def clear_collection():
    coll = get_collection()
    try:
        coll.delete(where={})
    except Exception:
        pass

def guess_source_from_path(path: str) -> str:
    p = path.replace("\\", "/").lower()
    if "/sessions/" in p: return "live-session"
    if "/blog_cpa/" in p or "/blog/cpa/" in p: return "blog-cpa"
    if "/blog_rrjr/" in p or "/blog/rrjr/" in p: return "blog-rrjr"
    return "doc"

# ---------------- Indexing ----------------
def index():
    ensure_metrics_db()

    print("Indexing from:", RAW_ROOT)
    files = gather_files(RAW_ROOT)
    print(f"Found {len(files)} files to index.")
    coll = get_collection()

    total_chunks = 0
    for path in files:
        meta, body = read_file_text(path)
        if not body.strip():
            continue

        title = title_from_meta_or_path(meta, path)
        doc_id = file_id(path)

        base_meta = {
            "title":        normalize_scalar(title),
            "path":         normalize_scalar(path),
            "source":       normalize_scalar(meta.get("source", guess_source_from_path(path))),
            "last_indexed": normalize_scalar(now_iso()),
        }
        for k in ("tags", "categories", "url", "video_url", "last_updated", "role"):
            if k in meta:
                base_meta[k] = normalize_scalar(meta[k])

        # chunk & simple stats
        chunks = chunk_text(body, CHUNK_TOKENS, CHUNK_OVERLAP)
        if not chunks:
            continue
        chars  = len(body)
        tokens = len(tokenize(body))
        chunk_count = len(chunks)

        # embed and upsert to Chroma
        _ = embed_all(chunks, batch_size=BATCH_SIZE)
        ids = [make_chunk_id(doc_id, i) for i in range(len(chunks))]
        metadatas = [{**base_meta, "chunk_index": i} for i in range(len(chunks))]
        coll.upsert(ids=ids, documents=chunks, metadatas=[normalize_metadata(m) for m in metadatas])

        # upsert to metrics DB
        upsert_document_row({
            "doc_id":       doc_id,
            "title":        base_meta["title"],
            "path":         base_meta["path"],
            "source":       base_meta["source"],
            "tags":         normalize_scalar(meta.get("tags")),
            "categories":   normalize_scalar(meta.get("categories")),
            "url":          normalize_scalar(meta.get("url")),
            "video_url":    normalize_scalar(meta.get("video_url")),
            "last_updated": normalize_scalar(meta.get("last_updated")),
            "chars":        chars,
            "tokens":       tokens,
            "chunk_count":  chunk_count,
            "last_indexed": base_meta["last_indexed"],
        })

        total_chunks += len(chunks)
        print(f"Indexed: {title}  ({len(chunks)} chunks)")

    print(f"\nDone. Total chunks: {total_chunks}")
    try:
        print("Chroma count:", get_collection().count())
    except Exception:
        pass

# ---------------- Main ----------------
if __name__ == "__main__":
    if "--no-clear" not in sys.argv:
        print("Clearing existing vectors …")
        clear_collection()
    index()