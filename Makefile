.PHONY: help test ingest ingest-no-enrich install-dev install-ingest ingest-fs

CHANNELS?=data/channels/islamic_kids.csv
OUT?=out/islamic_kids
LIMIT?=25

# Select Python/pip executable (override with: make PY=python)
PY?=python3
PIP?=pip3

help:
	@echo "Targets:"
	@echo "  test                Run unit tests (pytest)"
	@echo "  ingest              Run ingest with enrichment (uses .env if present)"
	@echo "  ingest-no-enrich    Run ingest without videos.list enrichment"
	@echo "  ingest-fs           Ingest and write to Firestore (requires LUMENS_GCP_PROJECT and ADC)"
	@echo "  install-dev         Install dev deps (pytest)"
	@echo "  install-ingest      Install optional ingest deps (google-cloud-firestore)"
	@echo ""
	@echo "Variables:"
	@echo "  PY=$(PY) (override with PY=python)"
	@echo "  PIP=$(PIP) (override with PIP=pip)"

test:
	$(PIP) install -r requirements-dev.txt
	pytest -q

install-dev:
	$(PIP) install -r requirements-dev.txt

install-ingest:
	$(PIP) install -r requirements-ingest.txt || $(PIP) install google-cloud-firestore

ingest:
	$(PY) -m services.ingest.cli --channels $(CHANNELS) --out $(OUT) --limit $(LIMIT)

ingest-no-enrich:
	$(PY) -m services.ingest.cli --channels $(CHANNELS) --out $(OUT) --limit $(LIMIT) --no-enrich

# Example: make ingest-fs LIMIT=10 LUMENS_GCP_PROJECT=lumens-alnayeem-dev
ingest-fs:
	@if [ -z "$$LUMENS_GCP_PROJECT" ]; then echo "Set LUMENS_GCP_PROJECT or pass --firestore-project"; exit 2; fi
	$(PY) -m services.ingest.cli --channels $(CHANNELS) --out $(OUT) --limit $(LIMIT) --firestore-project $$LUMENS_GCP_PROJECT
