import os
import sys
import pathlib
import threading
import subprocess
import sqlite3
import json
from datetime import datetime, timedelta
from fastapi import FastAPI, Request, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from openai import OpenAI
from dotenv import load_dotenv
import chromadb
from chromadb.config import Settings
import hashlib
import time
import importlib.util

load_dotenv()

# === Setup ===
BASE_DIR = pathlib.Path(__file__).resolve().parents[1]
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "supersecret123")

# ChromaDB settings (matching your build_index.py)
CHROMA_DIR = os.getenv("CHROMA_DIR", str(BASE_DIR / "data" / "chroma"))
COLLECTION_NAME = os.getenv("CHROMA_COLLECTION", "academy_kb")
EMBED_MODEL = os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-small")
METRICS_DB = os.getenv("METRICS_DB", str(BASE_DIR / "data" / "telemetry.db"))

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

# Initialize ChromaDB
chroma_client = chromadb.PersistentClient(
    path=CHROMA_DIR,
    settings=Settings(allow_reset=True)
)

app = FastAPI(title="Academy KB API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# === Initialize Database Tables ===
def init_database():
    """Initialize all required database tables"""
    os.makedirs(os.path.dirname(METRICS_DB), exist_ok=True)
    con = sqlite3.connect(METRICS_DB)
    cur = con.cursor()
    
    # Documents table (existing)
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
      last_indexed TEXT,
      status TEXT DEFAULT 'indexed'
    )
    """)
    
    # Query logs for analytics
    cur.execute("""
    CREATE TABLE IF NOT EXISTS query_logs (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      user_id TEXT,
      query TEXT,
      response_time REAL,
      tokens_used INTEGER,
      timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Text training data
    cur.execute("""
    CREATE TABLE IF NOT EXISTS text_training (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      content TEXT,
      character_count INTEGER,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Q&A pairs
    cur.execute("""
    CREATE TABLE IF NOT EXISTS qa_pairs (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      question TEXT,
      answer TEXT,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      used_count INTEGER DEFAULT 0
    )
    """)
    
    con.commit()
    con.close()

# Initialize database on startup
init_database()

# === Indexing Functions ===
def load_indexing_module():
    """Dynamically load the indexing module to avoid circular imports"""
    script_path = BASE_DIR / "scripts" / "build_index.py"
    spec = importlib.util.spec_from_file_location("build_index", script_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def index_single_file(file_path: str, filename: str) -> Dict:
    """Index a single uploaded file"""
    try:
        # Load indexing functions
        indexer = load_indexing_module()
        
        # Read and parse the file
        meta, text = indexer.read_file_text(file_path)
        if not text.strip():
            return {"status": "error", "message": "File appears to be empty"}
        
        # Generate document ID and metadata
        doc_id = indexer.file_id(file_path)
        title = indexer.title_from_meta_or_path(meta, filename)
        
        # Tokenize and chunk
        tokens = indexer.tokenize(text)
        chunk_texts = indexer.chunk_text(text, indexer.CHUNK_TOKENS, indexer.CHUNK_OVERLAP)
        
        if not chunk_texts:
            return {"status": "error", "message": "Could not create chunks from file"}
        
        # Create embeddings
        embeddings = indexer.embed_all(chunk_texts)
        
        # Get collection
        collection = indexer.get_collection()
        
        # Prepare data for ChromaDB
        chunk_ids = [indexer.make_chunk_id(doc_id, i) for i in range(len(chunk_texts))]
        
        # Base metadata for all chunks
        base_meta = {
            "doc_id": doc_id,
            "title": title,
            "path": f"uploads/{filename}",
            "source": "upload",
            "last_indexed": indexer.now_iso(),
        }
        
        # Normalize metadata
        normalized_meta = indexer.normalize_metadata({**meta, **base_meta})
        chunk_metas = [normalized_meta for _ in range(len(chunk_texts))]
        
        # Add chunk index to each metadata
        for i, chunk_meta in enumerate(chunk_metas):
            chunk_meta["chunk_index"] = i
        
        # Upsert to ChromaDB
        collection.upsert(
            ids=chunk_ids,
            documents=chunk_texts,
            embeddings=embeddings,
            metadatas=chunk_metas
        )
        
        # Update document tracking database
        indexer.upsert_document_row({
            "doc_id": doc_id,
            "title": title,
            "path": f"uploads/{filename}",
            "source": "upload",
            "tags": indexer.normalize_scalar(meta.get("tags")),
            "categories": indexer.normalize_scalar(meta.get("categories")),
            "url": indexer.normalize_scalar(meta.get("url")),
            "video_url": indexer.normalize_scalar(meta.get("video_url")),
            "last_updated": indexer.normalize_scalar(meta.get("last_updated")),
            "chars": len(text),
            "tokens": len(tokens),
            "chunk_count": len(chunk_texts),
            "last_indexed": base_meta["last_indexed"],
            "status": "indexed"
        })
        
        return {
            "status": "indexed",
            "doc_id": doc_id,
            "title": title,
            "chunks": len(chunk_texts),
            "tokens": len(tokens)
        }
        
    except Exception as e:
        print(f"Error indexing file {filename}: {e}")
        return {"status": "error", "message": str(e)}

# === Models ===
class QueryIn(BaseModel):
    query: str
    top_k: Optional[int] = 5
    user_id: Optional[str] = None

class Source(BaseModel):
    title: Optional[str] = None
    path: Optional[str] = None
    url: Optional[str] = None
    source: Optional[str] = None

class QueryOut(BaseModel):
    answer: str
    sources: List[Source]

class TextTrainingIn(BaseModel):
    content: str

class QAPairIn(BaseModel):
    question: str
    answer: str

# === Utils ===
def _require_admin(req: Request):
    auth = req.headers.get("authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing token")
    token = auth.split(" ", 1)[1].strip()
    if token != ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="Forbidden")

def get_collection():
    """Get or create the ChromaDB collection"""
    try:
        return chroma_client.get_collection(COLLECTION_NAME)
    except Exception:
        return None

def embed_query(text: str) -> List[float]:
    """Embed a query using OpenAI"""
    try:
        response = client.embeddings.create(
            model=EMBED_MODEL,
            input=text
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"Embedding error: {e}")
        raise HTTPException(status_code=500, detail="Failed to create embedding")

def generate_url_from_title(title: str, source: str = None, path: str = None) -> Optional[str]:
    """Generate URL from title and metadata if not provided"""
    if not title:
        return None
    
    import re
    
    def slugify(text):
        """Convert title to URL slug"""
        slug = re.sub(r'[^\w\s-]', '', text.lower())
        slug = re.sub(r'[-\s]+', '-', slug)
        return slug.strip('-')
    
    slug = slugify(title)
    
    # Determine site based on source or content
    if source == "blog-rrjr" or (path and "robertrodriguezjr" in path):
        return f"https://robertrodriguezjr.com/{slug}/"
    elif source == "blog-cpa" or (path and "creativepathworkshops" in path):
        return f"https://creativepathworkshops.com/{slug}/"
    elif source in ["blog-rrjr", "upload"] or any(word in title.lower() for word in 
        ["photo", "lightroom", "print", "workshop", "landscape", "composition", "academy"]):
        # Default to robertrodriguezjr.com for photography content
        return f"https://robertrodriguezjr.com/{slug}/"
    
    return None

def log_query(user_id: str, query: str, response_time: float, tokens_used: int = 0):
    """Log a query for analytics"""
    try:
        con = sqlite3.connect(METRICS_DB)
        cur = con.cursor()
        cur.execute("""
            INSERT INTO query_logs (user_id, query, response_time, tokens_used)
            VALUES (?, ?, ?, ?)
        """, (user_id, query, response_time, tokens_used))
        con.commit()
        con.close()
    except Exception as e:
        print(f"Failed to log query: {e}")

# === Original Endpoints ===
@app.post("/query", response_model=QueryOut)
async def query(data: QueryIn):
    """Query the knowledge base"""
    start_time = time.time()
    collection = get_collection()
    
    if not collection:
        return QueryOut(
            answer="The knowledge base has not been indexed yet. Please run the indexer first.",
            sources=[]
        )
    
    try:
        # Check Q&A pairs first
        con = sqlite3.connect(METRICS_DB)
        cur = con.cursor()
        cur.execute("""
            SELECT answer FROM qa_pairs 
            WHERE LOWER(question) = LOWER(?)
            LIMIT 1
        """, (data.query,))
        qa_result = cur.fetchone()
        con.close()
        
        if qa_result:
            response_time = time.time() - start_time
            log_query(data.user_id or "anonymous", data.query, response_time)
            return QueryOut(answer=qa_result[0], sources=[])
        
        # Regular ChromaDB search
        query_embedding = embed_query(data.query)
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=data.top_k,
            include=["documents", "metadatas", "distances"]
        )
        
        if not results["documents"] or not results["documents"][0]:
            return QueryOut(
                answer="I couldn't find any relevant information in the knowledge base for your query.",
                sources=[]
            )
        
        contexts = []
        sources_dict = {}
        
        for doc, metadata in zip(results["documents"][0], results["metadatas"][0]):
            contexts.append(doc)
            title = metadata.get("title", "Unknown")
            if title not in sources_dict:
                # Get URL from metadata or generate it
                url = metadata.get("url")
                if not url:
                    url = generate_url_from_title(
                        title, 
                        metadata.get("source"), 
                        metadata.get("path")
                    )
                
                sources_dict[title] = Source(
                    title=title,
                    path=metadata.get("path"),
                    url=url,
                    source=metadata.get("source", "doc")
                )
        
        context_text = "\n\n---\n\n".join(contexts[:data.top_k])
        
        # Use a default style guide if prompts module isn't available
        try:
            from prompts import STYLE_GUIDE
        except ImportError:
            try:
                from app.prompts import STYLE_GUIDE
            except ImportError:
                # Fallback style guide
                STYLE_GUIDE = """
You are Robert Rodriguez Jr's Academy Assistant. Tone: clear, practical, encouraging.
Answer ONLY from provided context. If missing, say you don't know and suggest the closest lesson.
Format:
1) Summary (3–6 sentences)
2) How to apply (bulleted steps)
3) Sources (title + deep link + timestamp/page if present)
Keep citations precise.
"""
        system_prompt = STYLE_GUIDE
        user_prompt = f"""Question: {data.query}

Context from Academy Knowledge Base:
{context_text}

Provide an answer following the format guidelines (summary, how to apply, sources)."""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )
        
        answer = response.choices[0].message.content
        response_time = time.time() - start_time
        log_query(data.user_id or "anonymous", data.query, response_time, 500)
        
        return QueryOut(answer=answer, sources=list(sources_dict.values()))
        
    except Exception as e:
        print(f"Query error: {e}")
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")

@app.get("/index-status")
async def index_status():
    """Get the status of the vector index"""
    collection = get_collection()
    
    if not collection:
        return {
            "vector_count": 0,
            "last_indexed": None,
            "status": "No index found - please run indexer"
        }
    
    try:
        count = collection.count()
        con = sqlite3.connect(METRICS_DB)
        cur = con.cursor()
        cur.execute("SELECT MAX(last_indexed) FROM documents")
        result = cur.fetchone()
        con.close()
        last_indexed = result[0] if result else None
        
        return {
            "vector_count": count,
            "last_indexed": last_indexed,
            "status": "Index ready" if count > 0 else "Index empty"
        }
    except Exception as e:
        return {
            "vector_count": 0,
            "last_indexed": None,
            "status": f"Error: {str(e)}"
        }

@app.post("/reindex")
async def reindex(request: Request):
    """Trigger a reindex of the knowledge base"""
    _require_admin(request)

    def _run():
        try:
            script_path = BASE_DIR / "scripts" / "build_index.py"
            subprocess.run(
                [sys.executable, str(script_path)],
                cwd=str(BASE_DIR),
                check=True,
                capture_output=True,
                text=True
            )
            print("Reindex completed successfully")
        except subprocess.CalledProcessError as e:
            print(f"Reindex failed: {e.stderr}")
        except Exception as e:
            print(f"Reindex error: {repr(e)}")

    threading.Thread(target=_run, daemon=True).start()
    return {"status": "started", "message": "Reindexing in background"}

# === New Dashboard Endpoints ===

@app.get("/admin/documents")
async def get_documents(request: Request):
    """Get all indexed documents"""
    _require_admin(request)
    
    try:
        con = sqlite3.connect(METRICS_DB)
        cur = con.cursor()
        cur.execute("""
            SELECT doc_id, title, path, chunk_count, last_indexed, status
            FROM documents
            ORDER BY last_indexed DESC
        """)
        rows = cur.fetchall()
        con.close()
        
        documents = []
        for row in rows:
            documents.append({
                "id": row[0],
                "title": row[1],
                "path": row[2],
                "chunk_count": row[3] or 0,
                "last_indexed": row[4],
                "status": row[5] or "indexed"
            })
        
        return {"documents": documents}
    except Exception as e:
        print(f"Error fetching documents: {e}")
        return {"documents": []}

@app.delete("/admin/document/{doc_id}")
async def delete_document(doc_id: str, request: Request):
    """Delete a document from the index"""
    _require_admin(request)
    
    try:
        # Remove from ChromaDB
        collection = get_collection()
        if collection:
            # Delete all chunks for this document
            collection.delete(where={"doc_id": doc_id})
        
        # Remove from database
        con = sqlite3.connect(METRICS_DB)
        cur = con.cursor()
        cur.execute("DELETE FROM documents WHERE doc_id = ?", (doc_id,))
        con.commit()
        con.close()
        
        return {"status": "deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/admin/metrics")
async def get_metrics(request: Request):
    """Get usage metrics for the dashboard"""
    _require_admin(request)
    
    try:
        con = sqlite3.connect(METRICS_DB)
        cur = con.cursor()
        
        # Get today's queries
        today = datetime.now().strftime('%Y-%m-%d')
        cur.execute("""
            SELECT COUNT(*) FROM query_logs 
            WHERE DATE(timestamp) = ?
        """, (today,))
        queries_today = cur.fetchone()[0]
        
        # Get this week's queries
        week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        cur.execute("""
            SELECT COUNT(*) FROM query_logs 
            WHERE DATE(timestamp) >= ?
        """, (week_ago,))
        queries_week = cur.fetchone()[0]
        
        # Get total queries
        cur.execute("SELECT COUNT(*) FROM query_logs")
        total_queries = cur.fetchone()[0]
        
        # Get active users
        cur.execute("""
            SELECT COUNT(DISTINCT user_id) FROM query_logs 
            WHERE DATE(timestamp) = ?
        """, (today,))
        active_users = cur.fetchone()[0]
        
        # Get average response time
        cur.execute("SELECT AVG(response_time) FROM query_logs")
        avg_response_time = cur.fetchone()[0] or 0
        
        # Get daily usage for chart
        cur.execute("""
            SELECT DATE(timestamp) as date, COUNT(*) as count
            FROM query_logs
            WHERE DATE(timestamp) >= ?
            GROUP BY DATE(timestamp)
            ORDER BY date
        """, (week_ago,))
        daily_usage = [{"date": row[0], "count": row[1]} for row in cur.fetchall()]
        
        # Get popular topics (simplified - just count query keywords)
        cur.execute("""
            SELECT query, COUNT(*) as count
            FROM query_logs
            GROUP BY query
            ORDER BY count DESC
            LIMIT 10
        """)
        popular_topics = [{"topic": row[0][:30], "count": row[1]} for row in cur.fetchall()]
        
        con.close()
        
        return {
            "total_queries": total_queries,
            "queries_today": queries_today,
            "queries_week": queries_week,
            "active_users": active_users,
            "avg_response_time": avg_response_time,
            "daily_usage": daily_usage,
            "popular_topics": popular_topics,
            "messages_sent": total_queries
        }
    except Exception as e:
        print(f"Error fetching metrics: {e}")
        return {
            "total_queries": 0,
            "queries_today": 0,
            "queries_week": 0,
            "active_users": 0,
            "avg_response_time": 0,
            "daily_usage": [],
            "popular_topics": [],
            "messages_sent": 0
        }

@app.post("/admin/text-training")
async def add_text_training(data: TextTrainingIn, request: Request):
    """Add text training data"""
    _require_admin(request)
    
    try:
        con = sqlite3.connect(METRICS_DB)
        cur = con.cursor()
        cur.execute("""
            INSERT INTO text_training (content, character_count)
            VALUES (?, ?)
        """, (data.content, len(data.content)))
        con.commit()
        con.close()
        
        # TODO: Actually index this content into ChromaDB
        
        return {"status": "saved", "characters": len(data.content)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/admin/qa-pairs")
async def get_qa_pairs(request: Request):
    """Get all Q&A pairs"""
    _require_admin(request)
    
    try:
        con = sqlite3.connect(METRICS_DB)
        cur = con.cursor()
        cur.execute("""
            SELECT id, question, answer, created_at, used_count
            FROM qa_pairs
            ORDER BY created_at DESC
        """)
        rows = cur.fetchall()
        con.close()
        
        qa_pairs = []
        for row in rows:
            qa_pairs.append({
                "id": row[0],
                "question": row[1],
                "answer": row[2],
                "created_at": row[3],
                "used_count": row[4]
            })
        
        return {"qa_pairs": qa_pairs}
    except Exception as e:
        print(f"Error fetching Q&A pairs: {e}")
        return {"qa_pairs": []}

@app.post("/admin/qa-pairs")
async def add_qa_pair(data: QAPairIn, request: Request):
    """Add a Q&A pair"""
    _require_admin(request)
    
    try:
        con = sqlite3.connect(METRICS_DB)
        cur = con.cursor()
        cur.execute("""
            INSERT INTO qa_pairs (question, answer)
            VALUES (?, ?)
        """, (data.question, data.answer))
        con.commit()
        con.close()
        
        return {"status": "saved"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/admin/qa-pairs/{qa_id}")
async def delete_qa_pair(qa_id: int, request: Request):
    """Delete a Q&A pair"""
    _require_admin(request)
    
    try:
        con = sqlite3.connect(METRICS_DB)
        cur = con.cursor()
        cur.execute("DELETE FROM qa_pairs WHERE id = ?", (qa_id,))
        con.commit()
        con.close()
        
        return {"status": "deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/admin/upload-document")
async def upload_document(request: Request, file: UploadFile = File(...)):
    """Upload and index a document"""
    _require_admin(request)
    
    try:
        # Validate file type
        allowed_extensions = {'.md', '.txt', '.pdf', '.docx', '.html', '.csv'}
        file_ext = pathlib.Path(file.filename).suffix.lower()
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported file type: {file_ext}. Allowed: {', '.join(allowed_extensions)}"
            )
        
        # Save the file
        upload_dir = BASE_DIR / "data" / "uploads"
        upload_dir.mkdir(exist_ok=True, parents=True)
        
        file_path = upload_dir / file.filename
        content = await file.read()
        
        with open(file_path, "wb") as f:
            f.write(content)
        
        # Index the uploaded file
        result = index_single_file(str(file_path), file.filename)
        
        if result["status"] == "error":
            # Clean up the file if indexing failed
            try:
                os.unlink(file_path)
            except:
                pass
            raise HTTPException(status_code=500, detail=f"Indexing failed: {result['message']}")
        
        return {
            "status": "uploaded_and_indexed",
            "filename": file.filename,
            "doc_id": result["doc_id"],
            "title": result["title"],
            "chunks": result["chunks"],
            "tokens": result["tokens"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        # Clean up file if something went wrong
        try:
            if 'file_path' in locals():
                os.unlink(file_path)
        except:
            pass
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/admin/sync-documents")
async def sync_documents(request: Request):
    """Sync document tracking database with ChromaDB contents"""
    _require_admin(request)
    
    try:
        collection = get_collection()
        if not collection:
            return {"status": "error", "message": "ChromaDB collection not found"}
        
        # Get all documents from ChromaDB
        result = collection.get(include=["metadatas"])
        
        if not result["ids"]:
            return {"status": "success", "message": "No documents found in ChromaDB", "synced": 0}
        
        # Group chunks by document ID
        doc_groups = {}
        for chunk_id, metadata in zip(result["ids"], result["metadatas"]):
            doc_id = metadata.get("doc_id")
            if doc_id:
                if doc_id not in doc_groups:
                    doc_groups[doc_id] = {
                        "chunks": [],
                        "metadata": metadata
                    }
                doc_groups[doc_id]["chunks"].append(chunk_id)
        
        # Update document tracking database
        con = sqlite3.connect(METRICS_DB)
        cur = con.cursor()
        
        synced_count = 0
        for doc_id, doc_info in doc_groups.items():
            meta = doc_info["metadata"]
            chunk_count = len(doc_info["chunks"])
            
            # Calculate estimated character count (rough estimate)
            estimated_chars = chunk_count * 800  # rough estimate
            estimated_tokens = chunk_count * 200  # rough estimate
            
            cur.execute("""
                INSERT OR REPLACE INTO documents 
                (doc_id, title, path, source, tags, categories, url, video_url, last_updated, chars, tokens, chunk_count, last_indexed, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                doc_id,
                meta.get("title", "Unknown Document"),
                meta.get("path", ""),
                meta.get("source", "unknown"),
                meta.get("tags", ""),
                meta.get("categories", ""),
                meta.get("url", ""),
                meta.get("video_url", ""),
                meta.get("last_updated", ""),
                estimated_chars,
                estimated_tokens,
                chunk_count,
                meta.get("last_indexed", ""),
                "indexed"
            ))
            synced_count += 1
        
        con.commit()
        con.close()
        
        return {
            "status": "success", 
            "message": f"Synced {synced_count} documents from {len(result['ids'])} chunks",
            "synced": synced_count,
            "total_chunks": len(result["ids"])
        }
        
    except Exception as e:
        print(f"Error syncing documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))