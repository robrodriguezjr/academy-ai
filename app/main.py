# app/main.py
import os
import sys
import json
import subprocess
from datetime import datetime
from threading import Lock

from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
from dotenv import load_dotenv
from openai import OpenAI

import chromadb
from llama_index.core import Settings, VectorStoreIndex
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore

# -------------- setup --------------
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Use the same embed model as your indexer
Settings.embed_model = OpenAIEmbedding(model="text-embedding-3-small")

# MUST match scripts/build_index.py
PERSIST_DIR = "./chroma_db"
COLLECTION = "academy_kb"
LAST_INDEXED_PATH = os.path.join(PERSIST_DIR, ".last_indexed")

# Miss logging
MISS_LOG_DIR = "data/logs"
MISS_LOG_PATH = os.path.join(MISS_LOG_DIR, "misses.jsonl")

# Strict mode threshold: if top score < this, we do NOT answer
SIMILARITY_THRESHOLD = float(os.getenv("KB_SIM_THRESHOLD", "0.78"))

app = FastAPI()
reindex_lock = Lock()


def get_index() -> VectorStoreIndex:
    db = chromadb.PersistentClient(path=PERSIST_DIR)
    coll = db.get_or_create_collection(COLLECTION)
    vs = ChromaVectorStore(chroma_collection=coll)
    return VectorStoreIndex.from_vector_store(vector_store=vs)


def _read_last_indexed() -> str | None:
    try:
        with open(LAST_INDEXED_PATH, "r", encoding="utf-8") as f:
            return f.read().strip() or None
    except Exception:
        return None


def _write_last_indexed() -> None:
    os.makedirs(PERSIST_DIR, exist_ok=True)
    ts = datetime.now().isoformat(timespec="seconds")
    try:
        with open(LAST_INDEXED_PATH, "w", encoding="utf-8") as f:
            f.write(ts)
    except Exception:
        pass


def _log_miss(payload: dict) -> None:
    try:
        os.makedirs(MISS_LOG_DIR, exist_ok=True)
        with open(MISS_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")
    except Exception:
        pass


# -------------- models --------------
class QueryRequest(BaseModel):
    query: str


# -------------- routes --------------
@app.get("/")
def root():
    return {"status": "ok", "message": "Academy KB API running"}


@app.post("/query")
def query_kb(body: QueryRequest):
    index = get_index()
    retriever = index.as_retriever(similarity_top_k=10)
    nodes = retriever.retrieve(body.query)

    # Pull top score (if present)
    top_score = 0.0
    if nodes:
        try:
            # LlamaIndex NodeWithScore.score: higher is better (similarity/cos sim)
            top_score = float(nodes[0].score or 0.0)
        except Exception:
            top_score = 0.0

    def pick(m: dict) -> dict:
        return {
            "title": m.get("title"),
            "source_url": m.get("source_url"),
            "tags": m.get("tags"),
            "category": m.get("category"),
            "last_updated": m.get("last_updated"),
            "relpath": m.get("relpath"),
            "filename": m.get("filename"),
            "ext": m.get("ext"),
        }

    # If below threshold → strict fallback (no answer)
    if top_score < SIMILARITY_THRESHOLD:
        # Build suggestions (closest 3 titles + short snippet)
        suggestions = []
        for n in nodes[:3]:
            m = n.metadata or {}
            text = (n.text or "").strip().split("\n", 1)[0]
            suggestions.append(
                {
                    "title": m.get("title") or m.get("filename") or "Untitled",
                    "source_url": m.get("source_url"),
                    "last_updated": m.get("last_updated"),
                    "snippet": text[:200],
                    **pick(m),
                }
            )

        # Generate 3 alternate phrasings (lightweight)
        rephrases = []
        try:
            prompt = (
                "You are helping a user rewrite a question for better retrieval in a knowledge base. "
                "Suggest three concise alternative phrasings that might match similar concepts, "
                "without adding new information.\n\n"
                f"Original question: {body.query}\n\n"
                "Return as a simple numbered list."
            )
            r = client.chat.completions.create(
                model="gpt-4o-mini",
                temperature=0.2,
                messages=[{"role": "user", "content": prompt}],
            )
            text = r.choices[0].message.content or ""
            # Split on lines that look like a list
            for line in text.splitlines():
                line = line.strip(" -\t")
                if not line:
                    continue
                # strip leading numbers like "1. "
                if line[:2].isdigit() or (len(line) > 2 and line[1] == "."):
                    line = line.split(".", 1)[-1].strip()
                rephrases.append(line)
            rephrases = [p for p in rephrases if p][:3]
        except Exception:
            rephrases = []

        # Log the miss
        _log_miss(
            {
                "ts": datetime.utcnow().isoformat() + "Z",
                "query": body.query,
                "top_score": top_score,
                "suggestions": [s.get("title") for s in suggestions],
            }
        )

        return {
            "answer": None,             # <-- strict: no general fallback
            "sources": [],              # nothing authoritative to cite
            "suggestions": suggestions, # nearby titles/snippets
            "rephrases": rephrases,     # 3 alternates
            "strict": True,
            "top_score": top_score,
            "threshold": SIMILARITY_THRESHOLD,
        }

    # Otherwise → build context & answer from KB
    def meta_block(m: dict) -> str:
        return (
            f"Title: {m.get('title','')}\n"
            f"URL: {m.get('source_url','')}\n"
            f"Tags: {', '.join(m.get('tags', []) or [])}\n"
            f"Category: {m.get('category','')}\n"
            f"Last Updated: {m.get('last_updated','')}\n"
            f"File: {m.get('relpath') or m.get('filename','')}\n"
        )

    blocks = []
    for n in nodes:
        m = n.metadata or {}
        blocks.append(meta_block(m) + "—\n" + (n.text or ""))

    context = "\n\n".join(blocks) if blocks else "No context retrieved."
    prompt = (
        "You are Robert Rodriguez Jr’s Academy KB assistant. "
        "Answer clearly and practically for photographers. "
        "Only use the provided context; if the context is insufficient, say you don’t know. "
        "Prefer citing specific titles in natural language.\n\n"
        f"Context:\n{context}\n\n"
        f"Question: {body.query}\n"
        "Answer:"
    )

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.2,
        messages=[{"role": "user", "content": prompt}],
    )
    answer = resp.choices[0].message.content

    sources = [pick(n.metadata or {}) for n in nodes]
    return {
        "answer": answer,
        "sources": sources,
        "strict": True,
        "top_score": top_score,
        "threshold": SIMILARITY_THRESHOLD,
    }


@app.post("/reindex")
def reindex(background_tasks: BackgroundTasks):
    if not reindex_lock.acquire(blocking=False):
        return {"status": "already_running"}

    def _run():
        try:
            subprocess.run([sys.executable, "scripts/build_index.py"], check=False)
            _write_last_indexed()
        finally:
            try:
                reindex_lock.release()
            except Exception:
                pass

    background_tasks.add_task(_run)
    return {"status": "started"}


@app.get("/stats")
def stats():
    db = chromadb.PersistentClient(path=PERSIST_DIR)
    coll = db.get_or_create_collection(COLLECTION)
    return {
        "count": coll.count(),
        "last_indexed": _read_last_indexed(),
        "similarity_threshold": SIMILARITY_THRESHOLD,
    }