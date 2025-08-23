# scripts/build_index.py
import os, re, time, shutil, csv
from typing import Dict, Any, Tuple, List

from dotenv import load_dotenv
load_dotenv()

import chromadb
from llama_index.core import Document, VectorStoreIndex
from llama_index.core.storage import StorageContext
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore

import yaml
from markdownify import markdownify as md_from_html
from pypdf import PdfReader
import docx  # python-docx

# ----- paths (MUST match app/main.py for PERSIST_DIR/COLLECTION) -----
PERSIST_DIR = "./chroma_db"
COLLECTION  = "academy_kb"
RAW_ROOT    = "data/raw"          # <- we index EVERYTHING under here
IGNORE_DIR_NAMES = {"_assets"}     # folders to skip anywhere in the tree

# ----- helpers -----
def read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def parse_front_matter(text: str) -> Tuple[Dict[str, Any], str]:
    """Parse YAML front matter if present and return (meta, body)."""
    if text.startswith("---\n"):
        m = re.search(r"^---\n(.*?)\n---\n", text, flags=re.DOTALL)
        if m:
            meta_raw = m.group(1)
            try:
                meta = yaml.safe_load(meta_raw) or {}
            except Exception:
                meta = {}
            body = text[m.end():]
            return meta, body
    return {}, text

def load_md_or_txt(path: str) -> Tuple[Dict[str, Any], str]:
    meta, body = parse_front_matter(read_text(path))
    return meta, body

def load_html(path: str) -> Tuple[Dict[str, Any], str]:
    meta, body = parse_front_matter(read_text(path))
    try:
        body_md = md_from_html(body or "")
    except Exception:
        body_md = body
    return meta, body_md

def load_pdf(path: str) -> Tuple[Dict[str, Any], str]:
    reader = PdfReader(path)
    parts: List[str] = []
    for p in reader.pages:
        try:
            parts.append(p.extract_text() or "")
        except Exception:
            parts.append("")
    return {}, "\n\n".join(parts)

def load_docx(path: str) -> Tuple[Dict[str, Any], str]:
    d = docx.Document(path)
    parts = [p.text for p in d.paragraphs]
    return {}, "\n\n".join(parts)

def load_csv(path: str) -> Tuple[Dict[str, Any], str]:
    """Turn CSV into a readable markdown block.
       If columns are exactly ['question','answer'] (case-insensitive), format as Q&A.
       Otherwise render a simple markdown table.
    """
    with open(path, "r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        rows = list(reader)

    if not rows:
        return {}, ""

    headers = [h.strip() for h in rows[0]]
    lower = [h.lower() for h in headers]
    body = ""

    if lower == ["question", "answer"]:
        lines = []
        for r in rows[1:]:
            if not any(r):
                continue
            q = (r[0] or "").strip()
            a = (r[1] or "").strip()
            if q or a:
                lines.append(f"### Q: {q}\nA: {a}\n")
        body = "\n".join(lines)
    else:
        # simple markdown table
        sep = "|" + "|".join([" --- " for _ in headers]) + "|\n"
        head = "|" + "|".join(headers) + "|\n"
        body_rows = []
        for r in rows[1:]:
            body_rows.append("|" + "|".join((cell or "").strip() for cell in r) + "|")
        body = head + sep + "\n".join(body_rows)

    return {}, body

LOADERS = {
    ".md":   load_md_or_txt,
    ".txt":  load_md_or_txt,
    ".html": load_html,
    ".htm":  load_html,
    ".pdf":  load_pdf,
    ".docx": load_docx,
    ".csv":  load_csv,
}

def iso_date_from_mtime(path: str) -> str:
    # YYYY-MM-DD
    return time.strftime("%Y-%m-%d", time.localtime(os.path.getmtime(path)))

def should_ignore_path(path: str) -> bool:
    parts = os.path.normpath(path).split(os.sep)
    if any(p.startswith(".") for p in parts):
        return True
    if any(p in IGNORE_DIR_NAMES for p in parts):
        return True
    return False

def make_source_url(full_path: str) -> str:
    rel = os.path.relpath(full_path, RAW_ROOT).replace(os.sep, "/")
    return f"/raw/{rel}"

def make_document(path: str) -> Document:
    ext = os.path.splitext(path)[1].lower()
    loader = LOADERS.get(ext)
    if not loader:
        raise SystemExit(f"Unsupported file type encountered: {path}")

    meta, text = loader(path)

    name = os.path.basename(path)
    title = meta.get("title") or os.path.splitext(name)[0]
    tags = meta.get("tags") or []
    category = meta.get("category") or None
    source_url = meta.get("source_url") or make_source_url(path)
    last_updated = meta.get("last_updated") or iso_date_from_mtime(path)

    metadata = {
        "title": title,
        "tags": tags,
        "category": category,
        "source_url": source_url,
        "last_updated": last_updated,
        "filename": name,
        "ext": ext,
        # where it came from, relative to RAW_ROOT (handy for debugging)
        "relpath": os.path.relpath(path, RAW_ROOT).replace(os.sep, "/"),
    }
    return Document(text=text, metadata=metadata)

# ----- main -----
def main():
    # Walk everything under RAW_ROOT; include specific extensions only
    paths: List[str] = []
    exts = set(LOADERS.keys())

    for root, dirs, files in os.walk(RAW_ROOT):
        # prune dirs so os.walk skips ignored ones
        dirs[:] = [d for d in dirs if not should_ignore_path(os.path.join(root, d))]
        for fn in files:
            fp = os.path.join(root, fn)
            if should_ignore_path(fp):
                continue
            if os.path.splitext(fn)[1].lower() in exts:
                paths.append(fp)

    paths.sort()
    if not paths:
        raise SystemExit(f"No supported files found under {RAW_ROOT}")

    docs = [make_document(p) for p in paths]

    # Clean, idempotent rebuild
    try:
        if os.path.exists(PERSIST_DIR):
            shutil.rmtree(PERSIST_DIR, ignore_errors=True)
        os.makedirs(PERSIST_DIR, exist_ok=True)
    except Exception:
        pass

    client = chromadb.PersistentClient(path=PERSIST_DIR)
    coll = client.get_or_create_collection(COLLECTION)

    vs = ChromaVectorStore(chroma_collection=coll)
    storage = StorageContext.from_defaults(vector_store=vs)
    embed = OpenAIEmbedding(model="text-embedding-3-small")

    VectorStoreIndex.from_documents(docs, storage_context=storage, embed_model=embed)

    print(f"Indexed {len(docs)} files")
    print("Chroma count:", coll.count())
    sample = coll.get(limit=5, include=["metadatas"])
    titles = [m.get("title") for m in (sample.get("metadatas") or [])]
    print("Sample titles:", titles)

if __name__ == "__main__":
    main()