Perfect — let’s give your repo a nice **README.md** that documents the structure, setup, and purpose. This way, whether it’s you on your MacBook, PC, or even a collaborator down the road, everything is clear.

  

Here’s a starter README for your academy-ai repo:

```
# Academy AI

A custom knowledge base and assistant for the **Creative Path Academy**, built with:
- **Python (FastAPI + LlamaIndex + ChromaDB)** → backend knowledge server
- **Raycast extension** → front-end command for querying the knowledge base
- **OpenAI API** → used for embeddings and answering questions

---

## Project Structure
```

academy-ai/

│

├── app/                  # FastAPI server (MCP server)

│   ├── main.py

│   └── …

│

├── scripts/              # Utility scripts

│   ├── build_index.py    # Rebuilds vector index from raw docs

│   └── csv_sessions_to_md.py  # Converts CSV session exports to Markdown

│

├── data/

│   ├── raw/              # Source docs (Markdown, PDFs, etc.)

│   ├── index/            # Vector database (ignored in Git)

│   └── …

│

├── raycast-extension/    # Raycast extension frontend

│   ├── package.json

│   ├── src/index.tsx

│   └── …

│

├── requirements.txt      # Python dependencies

├── .gitignore

└── README.md

````
---

## Setup

### 1. Backend (Python server)

```bash
git clone git@github.com:robrodriguezjr/academy-ai.git
cd academy-ai

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
````

Copy .env.example → .env and add your secrets (e.g. OPENAI_API_KEY).

  

Run the server:

```
uvicorn app.main:app --port 8002 --reload
```

### **2. Raycast Extension**

```
cd raycast-extension
npm ci
ray develop
```

This connects Raycast to your local MCP server and lets you query the knowledge base directly.

---

## **Data Workflow**

1. Place raw files into data/raw/ (supports .md, .txt, .html, .pdf, .docx, .csv).
    
2. Run the index build script:
    

```
python scripts/build_index.py
```

3. Query via:
    
    - curl (manual test)
        
    - Raycast extension (frontend)
        
    

---

## **Notes**

- .env contains API keys and is not tracked by Git.
    
- .venv/ and data/index/ are also excluded from Git.
    
- SSH keys (key, key.pub) should **never** be committed.
    
- Each machine sets up its own environment separately.
    

---

## **Roadmap**

- Add transcript auto-processing pipeline
    
- Support incremental indexing (new docs only)
    
- Web-based frontend for members
    
- Fine-tuned workflows for session transcripts
    

---

## **License**

  

© Robert Rodriguez Jr

```
---

👉 Want me to generate the file for you and stage it in Git so you can just `git commit -m "Add README"` and push?
```