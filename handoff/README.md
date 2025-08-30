# Academy Companion - Project Handoff Summary

## Quick Start Guide for New Developer

### What This Is
Academy Companion is an AI chatbot for Creative Path Academy that answers member questions about photography and creative business using Robert Rodriguez Jr's extensive knowledge base (900+ blog posts, 60+ workshops, 50+ live sessions). It's a RAG system using ChromaDB for vector search and GPT-4o-mini for response generation.

### Current State
- ✅ WordPress plugin deployed and working for members
- ✅ Admin dashboard built and functional locally
- ⚠️ Railway backend deployed but having issues with admin endpoints (502 errors)
- ❌ No documents indexed in production (vector count: 0)
- ✅ Local development environment fully functional

### Critical First Steps
1. **Fix Railway deployment** - Check logs for startup errors
2. **Index documents** - Need to get content into production ChromaDB
3. **Test with real members** - Verify the complete flow works

### How to Take Over This Project

#### 1. Set Up Local Environment
```bash
# Clone repository
git clone https://github.com/robrodriguezjr/academy-ai.git
cd academy-ai

# Python backend setup
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Start backend
python -m uvicorn app.main:app --port 8002 --reload

# In another terminal - Dashboard setup
cd academy-dashboard
npm install
npm start
```

#### 2. Understand the Architecture
- **Backend**: FastAPI app serving API endpoints (`app/main.py`)
- **Vector DB**: ChromaDB storing document embeddings (`data/chroma/`)
- **Indexing**: Python script processing documents (`scripts/build_index.py`)
- **WordPress**: Plugin for member chat interface (`academy-companion-wp-plugin/`)
- **Dashboard**: React admin interface (`academy-dashboard/`)

#### 3. Key Files to Review
```
app/main.py                 # All API endpoints
app/prompts.py             # System prompt for AI responses
scripts/build_index.py     # Document processing pipeline
academy-dashboard/src/Dashboard.tsx  # Admin interface
academy-companion-wp-plugin/js/chat.js  # User chat widget
```

#### 4. Current Issues to Fix
- **Railway 502 errors**: Admin endpoints failing in production
- **No indexed content**: Production ChromaDB is empty
- **Upload not triggering indexing**: Documents upload but don't get processed
- **Dashboard auth**: Using hardcoded token, needs proper authentication

### Project Files in This Handoff

1. **PROJECT_SPEC.md** - What the project does and why
2. **SYSTEM_PROMPT.md** - How the AI should respond
3. **ARCHITECTURE.md** - Technical structure and data flow
4. **PROMPTS/** - Example prompts and expected outputs
5. **TOOLING.md** - Development environment and commands
6. **EVAL.md** - Test cases and quality metrics
7. **DECISIONS.md** - Why things were built this way
8. **TODO.md** - Prioritized list of what needs doing

### Key Technologies
- **Backend**: Python 3.11, FastAPI, ChromaDB, OpenAI API
- **Frontend**: React 18, TypeScript, Recharts
- **Deployment**: Railway (backend), WordPress (user interface)
- **Models**: GPT-4o-mini (generation), text-embedding-3-small (vectors)

### Environment Variables Needed
```env
OPENAI_API_KEY=sk-...      # OpenAI API key
ADMIN_TOKEN=supersecret123  # Admin authentication
CHROMA_DIR=data/chroma      # Vector database location
METRICS_DB=data/telemetry.db # Analytics database
```

### Contact & Resources
- **Production URL**: https://academy-ai-production.up.railway.app
- **GitHub**: https://github.com/robrodriguezjr/academy-ai
- **Railway Dashboard**: Access needed for deployment logs
- **WordPress Site**: Creative Path Academy (member area)

### Success Criteria
The handoff is complete when:
1. New developer can run the project locally
2. Documents are indexed in production
3. Members can ask questions and get responses
4. Admin can view analytics and manage content
5. All golden test cases pass

### Final Notes
This project is at a critical transition point - the infrastructure is built but needs production debugging and content indexing. The highest priority is getting documents indexed so members can start using it. The WordPress plugin is already live and members are waiting for it to work.

The codebase is functional but needs production hardening. Focus on stability over new features initially. Once working, there's significant room for enhancement (see TODO.md for roadmap).

Robert's teaching philosophy emphasizes practical, encouraging guidance. The AI should maintain this voice while only answering from the indexed knowledge base, never inventing information.

Good luck! The foundation is solid; it just needs the final deployment issues resolved.