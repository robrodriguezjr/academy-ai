# --------- config (edit paths below to match your CSV locations) ---------
VENV=.venv
PY=$(VENV)/bin/python
PIP=$(VENV)/bin/pip

# CSV inputs
SESSIONS_CSV=data/imports/Live-Sessions-Export-2025-August-23-1135.csv
CPA_CSV=data/imports/cpa-posts.csv
RRJR_CSV=data/imports/rrjr-posts.csv

# Output folders
SESSIONS_OUT=data/raw/docs/sessions
CPA_OUT=data/raw/docs/blog/cpa
RRJR_OUT=data/raw/docs/blog/rrjr

TRANSCRIPTS_DIR=data/raw/transcripts

PORT?=8002

# --------- convenience targets ---------

# 1) Create venv and install deps
.PHONY: setup
setup: $(VENV)/bin/activate

$(VENV)/bin/activate:
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt || true
	# ensure markdownify for CSV -> MD
	$(PIP) install markdownify

# 2) Convert CSVs -> Markdown
.PHONY: sessions
sessions: setup
	$(PY) scripts/csv_to_md_multi.py \
		--kind live \
		--csv $(SESSIONS_CSV) \
		--out $(SESSIONS_OUT) \
		--transcripts-dir $(TRANSCRIPTS_DIR)

.PHONY: blog-cpa
blog-cpa: setup
	$(PY) scripts/csv_to_md_multi.py \
		--kind blog --site cpa \
		--csv $(CPA_CSV) \
		--out $(CPA_OUT)

.PHONY: blog-rrjr
blog-rrjr: setup
	$(PY) scripts/csv_to_md_multi.py \
		--kind blog --site rrjr \
		--csv $(RRJR_CSV) \
		--out $(RRJR_OUT)

# 3) Rebuild vector index from data/raw
.PHONY: reindex
reindex: setup
	$(PY) scripts/build_index.py

# 4) Run the API locally
.PHONY: serve
serve: setup
	$(VENV)/bin/uvicorn app.main:app --port $(PORT) --reload

# 5) Housekeeping
.PHONY: clean-index
clean-index:
	rm -rf data/index/*
	mkdir -p data/index
	touch data/index/.keep

.PHONY: clean-venv
clean-venv:
	rm -rf $(VENV)

.PHONY: doctor
doctor:
	@echo "Python: " && python3 --version
	@echo "Venv Python: " && [ -f $(PY) ] && $(PY) --version || echo "no venv yet"
	@echo "OpenAI key in .env? " && grep -q '^OPENAI_API_KEY=' .env && echo "yes" || echo "missing"
	@echo "CSV files present?"
	@[ -f $(SESSIONS_CSV) ] && echo "  sessions: OK" || echo "  sessions: MISSING ($(SESSIONS_CSV))"
	@[ -f $(CPA_CSV) ] && echo "  blog-cpa: OK" || echo "  blog-cpa: MISSING ($(CPA_CSV))"
	@[ -f $(RRJR_CSV) ] && echo "  blog-rrjr: OK" || echo "  blog-rrjr: MISSING ($(RRJR_CSV))"