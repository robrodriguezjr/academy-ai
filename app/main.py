import os
import sys
import pathlib
import threading
import subprocess
import sqlite3
from datetime import datetime
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from openai import OpenAI
from dotenv import load_dotenv
import chromadb
from chromadb.config import Settings

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

# === Models ===
class QueryIn(BaseModel):
    query: str
    top_k: Optional[int] = 5

class Source(BaseModel):
    title: Optional[str] = None
    path: Optional[str] = None
    url: Optional[str] = None
    source: Optional[str] = None

class QueryOut(BaseModel):
    answer: str
    sources: List[Source]

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
        # Collection doesn't exist yet
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

def get_last_indexed():
    """Get the last indexed timestamp from the metrics DB"""
    try:
        if not os.path.exists(METRICS_DB):
            return None
        con = sqlite3.connect(METRICS_DB)
        cur = con.cursor()
        cur.execute("SELECT MAX(last_indexed) FROM documents")
        result = cur.fetchone()
        con.close()
        return result[0] if result else None
    except Exception:
        return None

# === Endpoints ===
@app.post("/query", response_model=QueryOut)
async def query(data: QueryIn):
    """Query the knowledge base"""
    collection = get_collection()
    
    if not collection:
        return QueryOut(
            answer="The knowledge base has not been indexed yet. Please run the indexer first.",
            sources=[]
        )
    
    try:
        # Embed the query
        query_embedding = embed_query(data.query)
        
        # Search ChromaDB
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
        
        # Extract context from results
        contexts = []
        sources_dict = {}  # Use dict to deduplicate by title
        
        for doc, metadata in zip(results["documents"][0], results["metadatas"][0]):
            contexts.append(doc)
            
            # Track unique sources by title
            title = metadata.get("title", "Unknown")
            if title not in sources_dict:
                sources_dict[title] = Source(
                    title=title,
                    path=metadata.get("path"),
                    url=metadata.get("url"),
                    source=metadata.get("source", "doc")
                )
        
        # Build context for the LLM
        context_text = "\n\n---\n\n".join(contexts[:data.top_k])
        
        # Generate answer using GPT with custom style guide
        from prompts import STYLE_GUIDE
        
        system_prompt = STYLE_GUIDE
        
        user_prompt = f"""Question: {data.query}

Context from Academy Knowledge Base:
{context_text}

Provide an answer following the format guidelines (summary, how to apply, sources)."""

        response = client.chat.completions.create(
            model="gpt-4o-mini",  # You can change this to gpt-4 if you prefer
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )
        
        answer = response.choices[0].message.content
        
        return QueryOut(
            answer=answer,
            sources=list(sources_dict.values())
        )
        
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
        last_indexed = get_last_indexed()
        
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