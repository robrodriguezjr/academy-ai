# Tooling & Development Environment

## Required Tools

### Core Development Tools
```bash
# Required versions
node >= 18.0.0
npm >= 9.0.0
python >= 3.11
git >= 2.30.0
```

### Python Environment Setup
```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # Mac/Linux
.venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

### Node Environment Setup
```bash
# Dashboard setup
cd academy-dashboard
npm install

# WordPress plugin development
cd academy-companion-wp-plugin
# No npm needed - pure JS/PHP
```

## Project Directory Structure
```
academy-companion-ai/
├── app/                        # Backend API
│   ├── main.py                # FastAPI application
│   └── prompts.py             # System prompts
├── scripts/                    # Utility scripts
│   ├── build_index.py         # Document indexing
│   ├── csv_to_md_multi.py    # CSV conversion
│   └── academy_site_scraper.py # Web scraping
├── data/                       # Data storage
│   ├── raw/                   # Source documents
│   ├── chroma/                # Vector database
│   └── telemetry.db          # Analytics database
├── academy-dashboard/          # React admin dashboard
│   ├── src/
│   └── package.json
├── academy-companion-wp-plugin/ # WordPress plugin
│   ├── academy-companion.php
│   ├── js/
│   └── css/
├── academy-companion-rayext/   # Raycast extension
│   ├── src/
│   └── package.json
└── requirements.txt           # Python dependencies
```

## Essential CLI Commands

### Backend Development
```bash
# Start development server
cd ~/Academy\ Companion-AI
source .venv/bin/activate
python -m uvicorn app.main:app --port 8002 --reload

# Run indexing
python scripts/build_index.py

# Clear and reindex
python scripts/build_index.py --no-clear

# Check API health
curl http://localhost:8002/index-status
```

### Dashboard Development
```bash
# Start dashboard dev server
cd academy-dashboard
npm start

# Build for production
npm run build

# Run tests
npm test
```

### WordPress Plugin
```bash
# Create plugin zip
cd ~/Academy\ Companion-AI
zip -r academy-companion-plugin.zip academy-companion-wp-plugin/

# Install via WP-CLI (if available)
wp plugin install academy-companion-plugin.zip --activate
```

### Raycast Extension
```bash
cd academy-companion-rayext
npm run dev     # Development mode
npm run build   # Build extension
```

## Railway Deployment

### Initial Setup
```bash
# Install Railway CLI
brew install railway  # Mac
# or
npm install -g @railway/cli

# Login and link project
railway login
railway link
```

### Deployment Commands
```bash
# Deploy from Git
git add .
git commit -m "Update message"
git push origin main
# Railway auto-deploys from GitHub

# Manual deployment
railway up

# View logs
railway logs

# Run commands in production
railway run python scripts/build_index.py

# Environment variables
railway variables set OPENAI_API_KEY=sk-...
railway variables set ADMIN_TOKEN=your-token
```

## Environment Variables

### Required Variables
```env
# .env file (local development)
OPENAI_API_KEY=sk-your-key-here
ADMIN_TOKEN=supersecret123
CHROMA_DIR=data/chroma
METRICS_DB=data/telemetry.db
EMBED_MODEL=text-embedding-3-small
CHUNK_TOKENS=1000
CHUNK_OVERLAP=100
```

### Railway Production Variables
```bash
OPENAI_API_KEY=sk-production-key
ADMIN_TOKEN=strong-random-token
PORT=8080  # Railway provides this
CHROMA_DIR=/data/chroma
METRICS_DB=/data/telemetry.db
```

## API Function Schemas

### Query Endpoint
```python
# POST /query
{
    "query": str,           # User's question
    "top_k": int = 5,      # Number of context chunks
    "user_id": str = None   # Optional user identifier
}

# Response
{
    "answer": str,          # Generated response
    "sources": [
        {
            "title": str,
            "path": str,
            "url": str,
            "source": str
        }
    ]
}
```

### Document Upload
```python
# POST /admin/upload-document
# Headers: Authorization: Bearer <token>
# Body: multipart/form-data with file field

# Response
{
    "status": "uploaded",
    "filename": str
}
```

### Metrics Endpoint
```python
# GET /admin/metrics
# Headers: Authorization: Bearer <token>

# Response
{
    "total_queries": int,
    "queries_today": int,
    "queries_week": int,
    "active_users": int,
    "avg_response_time": float,
    "daily_usage": [
        {"date": str, "count": int}
    ],
    "popular_topics": [
        {"topic": str, "count": int}
    ]
}
```

## Database Operations

### SQLite Direct Access
```bash
# Open database
sqlite3 data/telemetry.db

# Common queries
.tables  # List all tables
SELECT COUNT(*) FROM documents;
SELECT query, COUNT(*) as count FROM query_logs GROUP BY query ORDER BY count DESC LIMIT 10;
.quit
```

### ChromaDB Operations
```python
# Python script to inspect ChromaDB
import chromadb
client = chromadb.PersistentClient(path="data/chroma")
collection = client.get_collection("academy_kb")
print(f"Vector count: {collection.count()}")
```

## Testing Commands

### API Testing
```bash
# Test query endpoint
curl -X POST http://localhost:8002/query \
  -H "Content-Type: application/json" \
  -d '{"query": "How do I price my photography?"}'

# Test status
curl http://localhost:8002/index-status

# Test admin endpoint
curl http://localhost:8002/admin/documents \
  -H "Authorization: Bearer supersecret123"
```

### Load Testing
```bash
# Using Apache Bench
ab -n 100 -c 10 http://localhost:8002/index-status

# Using curl in loop
for i in {1..10}; do
  curl -X POST http://localhost:8002/query \
    -H "Content-Type: application/json" \
    -d '{"query": "test query '$i'"}'
done
```

## Debugging Tools

### Python Debugging
```python
# Add to main.py for debugging
import pdb; pdb.set_trace()  # Breakpoint

# Or use logging
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.debug(f"Variable value: {variable}")
```

### React Debugging
```javascript
// Add to React components
console.log('State:', this.state);
debugger;  // Breakpoint for browser DevTools

// Use React DevTools browser extension
```

### Railway Debugging
```bash
# View live logs
railway logs --tail

# SSH into container (if enabled)
railway shell

# Check deployment status
railway status
```

## Backup and Recovery

### Database Backup
```bash
# Backup SQLite database
cp data/telemetry.db backups/telemetry_$(date +%Y%m%d).db

# Backup ChromaDB
tar -czf backups/chroma_$(date +%Y%m%d).tar.gz data/chroma/

# Restore
cp backups/telemetry_20240828.db data/telemetry.db
tar -xzf backups/chroma_20240828.tar.gz -C data/
```

### Document Backup
```bash
# Backup raw documents
tar -czf backups/raw_docs_$(date +%Y%m%d).tar.gz data/raw/

# Sync to cloud storage
rsync -av data/raw/ backup-server:/backups/academy/
```