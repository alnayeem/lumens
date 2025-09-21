.PHONY: help test ingest ingest-no-enrich install-dev install-ingest ingest-fs

CHANNELS?=data/channels/islamic_kids.csv
OUT?=out/islamic_kids
LIMIT?=25

help:
	@echo "Targets:"
	@echo "  test                Run unit tests (pytest)"
	@echo "  ingest              Run ingest with enrichment (uses .env if present)"
	@echo "  ingest-no-enrich    Run ingest without videos.list enrichment"
	@echo "  ingest-fs           Ingest and write to Firestore (requires LUMENS_GCP_PROJECT and ADC)"
	@echo "  install-dev         Install dev deps (pytest)"
	@echo "  install-ingest      Install optional ingest deps (google-cloud-firestore)"

test:
	pip install -r requirements-dev.txt
	pytest -q

install-dev:
	pip install -r requirements-dev.txt

install-ingest:
	pip install -r requirements-ingest.txt || pip install google-cloud-firestore

ingest:
	python -m services.ingest.cli --channels $(CHANNELS) --out $(OUT) --limit $(LIMIT)

ingest-no-enrich:
	python -m services.ingest.cli --channels $(CHANNELS) --out $(OUT) --limit $(LIMIT) --no-enrich

# Example: make ingest-fs LIMIT=10 LUMENS_GCP_PROJECT=lumens-alnayeem-dev
ingest-fs:
	@if [ -z "$$LUMENS_GCP_PROJECT" ]; then echo "Set LUMENS_GCP_PROJECT or pass --firestore-project"; exit 2; fi
	python -m services.ingest.cli --channels $(CHANNELS) --out $(OUT) --limit $(LIMIT) --firestore-project $$LUMENS_GCP_PROJECT

