# Academy Companion - System Architecture

## Overview
Academy Companion is a RAG (Retrieval-Augmented Generation) system that combines vector similarity search with LLM response generation to provide contextual answers from a curated knowledge base.

## Architecture Diagram
```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│                 │     │                  │     │                 │
│  WordPress      │────▶│  FastAPI         │────▶│  ChromaDB       │
│  Plugin         │     │  Backend         │     │  Vector Store   │
│                 │     │                  │     │                 │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                               │                           │
                               ▼                           │
                        ┌──────────────────┐              │
                        │                  │              │
                        │  OpenAI API      │◀─────────────┘
                        │  GPT-4o-mini     │
                        │  Embeddings      │
                        └──────────────────┘
```

## Components

### 1. Frontend Interfaces

#### WordPress Plugin (`academy-companion-wp-plugin/`)
- **Purpose**: Member-facing chat interface
- **Technology**: JavaScript, PHP
- **Features**:
  - Authentication via WordPress user system
  - Chat widget with suggested questions
  - Session management for conversation context
  - Mobile-responsive design

#### Admin Dashboard (`academy-dashboard/`)
- **Purpose**: Content and analytics management
- **Technology**: React, TypeScript, Recharts
- **Features**:
  - Document upload and management
  - Usage analytics visualization
  - Q&A pairs management
  - Direct text training input

#### Raycast Extension (`academy-companion-rayext/`)
- **Purpose**: Local development and testing
- **Technology**: TypeScript, React
- **Features**:
  - Quick queries during development
  - Status checking
  - Manual reindexing triggers

### 2. Backend API (`app/main.py`)

#### Core Endpoints
```python
POST /query                 # Main chat endpoint
GET  /index-status          # Vector database status
POST /reindex              # Trigger full reindex
GET  /admin/documents      # List indexed documents
POST /admin/upload-document # Upload new content
GET  /admin/metrics        # Usage analytics
POST /admin/text-training  # Add training text
GET  /admin/qa-pairs       # Manage Q&A pairs
```

#### Key Responsibilities
- Query orchestration and response generation
- Document management and indexing coordination
- Usage tracking and analytics
- Authentication and authorization
- Rate limiting and error handling

### 3. Document Processing Pipeline (`scripts/build_index.py`)

#### Processing Flow
1. **Document Discovery**: Scan `data/raw/` for supported formats
2. **Content Extraction**: Parse MD, TXT, PDF, HTML, CSV files
3. **Metadata Extraction**: YAML frontmatter parsing
4. **Chunking**: Split into ~1000 token segments with 100 token overlap
5. **Embedding**: Generate vectors via OpenAI text-embedding-3-small
6. **Storage**: Upsert to ChromaDB with metadata

#### Supported Formats
- Markdown (.md) - Primary format with YAML frontmatter
- Text (.txt) - Plain text documents
- PDF (.pdf) - Extracted via PyPDF
- HTML (.html) - Converted to markdown
- Word (.docx) - Text extraction
- CSV (.csv) - Converted to JSON representation

### 4. Vector Database (ChromaDB)

#### Schema
```python
{
    "id": "doc_hash_00001",          # Unique chunk identifier
    "document": "chunk text content", # Actual text
    "embedding": [0.1, 0.2, ...],    # 1536-dim vector
    "metadata": {
        "title": "Document Title",
        "path": "data/raw/blog/post.md",
        "source": "blog-rrjr",
        "chunk_index": 0,
        "last_indexed": "2024-08-28T10:00:00Z",
        "tags": "portrait, lighting",
        "categories": "technique"
    }
}
```

#### Collections
- `academy_kb`: Main knowledge base collection
- Supports up to 200,000 vectors (current: ~2000)

### 5. Database Layer (SQLite)

#### Tables
```sql
-- Document tracking
CREATE TABLE documents (
    doc_id TEXT PRIMARY KEY,
    title TEXT,
    path TEXT,
    chunk_count INTEGER,
    last_indexed DATETIME,
    status TEXT -- 'indexed', 'pending', 'failed'
);

-- Usage analytics
CREATE TABLE query_logs (
    id INTEGER PRIMARY KEY,
    user_id TEXT,
    query TEXT,
    response_time REAL,
    tokens_used INTEGER,
    timestamp DATETIME
);

-- Q&A pairs
CREATE TABLE qa_pairs (
    id INTEGER PRIMARY KEY,
    question TEXT,
    answer TEXT,
    used_count INTEGER
);

-- Text training
CREATE TABLE text_training (
    id INTEGER PRIMARY KEY,
    content TEXT,
    character_count INTEGER,
    created_at DATETIME
);
```

## Data Flow

### Query Processing
1. **User Input**: Question submitted via WordPress/Dashboard
2. **Authentication**: Verify user access rights
3. **Q&A Check**: Search predefined Q&A pairs for exact match
4. **Embedding**: Generate query vector via OpenAI
5. **Vector Search**: Find top-k similar chunks in ChromaDB
6. **Context Assembly**: Combine relevant chunks
7. **LLM Generation**: Send context + query to GPT-4o-mini
8. **Response Formatting**: Structure as Summary/Application/Sources
9. **Logging**: Record query metrics for analytics
10. **Delivery**: Return formatted response to user

### Document Indexing
1. **Upload**: File received via dashboard or filesystem
2. **Validation**: Check format and size constraints
3. **Extraction**: Parse content and metadata
4. **Chunking**: Split into processable segments
5. **Embedding**: Batch generate vectors
6. **Storage**: Upsert to ChromaDB
7. **Tracking**: Update documents table
8. **Confirmation**: Return indexing status

## Technology Stack

### Core Technologies
- **Python 3.11**: Primary backend language
- **FastAPI**: Async web framework
- **ChromaDB**: Vector database for similarity search
- **OpenAI API**: Embeddings and completion
- **SQLite**: Metadata and analytics storage

### Frontend Stack
- **React 18**: Dashboard and chat components
- **TypeScript**: Type-safe frontend code
- **Recharts**: Data visualization
- **react-dropzone**: File upload handling

### Infrastructure
- **Railway**: Cloud hosting platform
- **GitHub**: Version control and CI/CD
- **Docker**: Containerization (via Railway)

### Key Dependencies
```txt
fastapi==0.104.1
uvicorn==0.24.0
chromadb==0.4.18
openai==1.3.7
tiktoken==0.5.2
pypdf==3.17.1
python-docx==1.1.0
markdownify==0.11.6
python-dotenv==1.0.0
```

## Deployment Architecture

### Production (Railway)
```yaml
Services:
  - academy-ai (FastAPI backend)
    - CPU: 1 vCPU
    - RAM: 512MB
    - Storage: 10GB persistent volume
    - Region: us-east

Environment Variables:
  - OPENAI_API_KEY
  - ADMIN_TOKEN
  - CHROMA_DIR=/data/chroma
  - METRICS_DB=/data/telemetry.db
```

### Local Development
```bash
# Backend
python -m uvicorn app.main:app --port 8002 --reload

# Dashboard
npm start # Port 3000

# Indexing
python scripts/build_index.py
```

## Security Considerations

### Authentication
- WordPress plugin uses native WP user authentication
- Admin endpoints require Bearer token
- Rate limiting on public endpoints

### Data Protection
- Embeddings stored locally (not sent to third parties)
- User queries logged anonymously
- CORS configured for specific domains

### API Security
- OpenAI API key server-side only
- No client-side API exposure
- Request validation and sanitization