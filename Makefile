.PHONY: help venv test ingest ingest-no-enrich install-dev install-ingest ingest-fs install-all resolve-channels ingest-cached query

CHANNELS?=data/channels/islamic_kids.csv
OUT?=out/islamic_kids
LIMIT?=25

# Select Python/pip executable (override with: make PY=python)
# Prefer repo-local virtualenv if present
PY?=$(if $(wildcard .venv/bin/python),.venv/bin/python,python3)
# Default pip to run under the same Python interpreter
PIP?=$(PY) -m pip

help:
	@echo "Targets:"
	@echo "  venv                Create a local virtualenv at ./.venv"
	@echo "  test                Run unit tests (pytest)"
	@echo "  ingest              Run ingest with enrichment (uses .env if present)"
	@echo "  ingest-no-enrich    Run ingest without videos.list enrichment"
	@echo "  ingest-fs           Ingest and write to Firestore (requires LUMENS_GCP_PROJECT and ADC)"
	@echo "  resolve-channels    Resolve channel refs to UCIDs and cache mapping"
	@echo "  ingest-cached       Ingest using cached channel mapping (avoids search quota)"
	@echo "  query               Query Firestore content and print or write NDJSON"
	@echo "  install-dev         Install dev deps (pytest)"
	@echo "  install-ingest      Install optional ingest deps (google-cloud-firestore)"
	@echo "  install-all         Install dev + ingest deps into current Python ($(PY))"
	@echo ""
	@echo "Variables:"
	@echo "  PY=$(PY) (override with PY=python)"
	@echo "  PIP=$(PIP) (override with PIP=pip)"

venv:
	python3 -m venv .venv
	.venv/bin/python -m pip install --upgrade pip
	@echo "Created venv at .venv. Re-run make commands; Makefile will use .venv/bin/python automatically."

test:
	$(PIP) install -r requirements-dev.txt
	pytest -q

install-dev:
	$(PIP) install -r requirements-dev.txt

install-ingest:
	$(PIP) install -r requirements-ingest.txt || $(PIP) install google-cloud-firestore

install-all: install-dev install-ingest

ingest:
	$(PY) -m services.ingest.cli --channels $(CHANNELS) --out $(OUT) --limit $(LIMIT)

ingest-no-enrich:
	$(PY) -m services.ingest.cli --channels $(CHANNELS) --out $(OUT) --limit $(LIMIT) --no-enrich

# Example: make ingest-fs LIMIT=10 LUMENS_GCP_PROJECT=lumens-alnayeem-dev
ingest-fs:
	@if [ -z "$$LUMENS_GCP_PROJECT" ]; then echo "Set LUMENS_GCP_PROJECT or pass --firestore-project"; exit 2; fi
	$(PY) -m services.ingest.cli --channels $(CHANNELS) --out $(OUT) --limit $(LIMIT) --firestore-project $$LUMENS_GCP_PROJECT

CHANNELS_MAP?=out/channels_map.json
STATE?=out/state.json

resolve-channels:
	$(PY) -m services.ingest.cli --channels $(CHANNELS) --resolve-out $(CHANNELS_MAP)

ingest-cached:
	$(PY) -m services.ingest.cli --channels $(CHANNELS) --channels-map $(CHANNELS_MAP) --state $(STATE) --out $(OUT) --limit $(LIMIT)

QUERY_CHANNEL?=
QUERY_TOPIC?=
QUERY_LIMIT?=25
QUERY_SINCE?=
QUERY_OUT?=

query:
	@if [ -z "$$LUMENS_GCP_PROJECT" ]; then echo "Set LUMENS_GCP_PROJECT or pass --project"; exit 2; fi
	$(PY) -m services.read.query_content --project $$LUMENS_GCP_PROJECT --channel "$(QUERY_CHANNEL)" --topic "$(QUERY_TOPIC)" --limit $(QUERY_LIMIT) --since "$(QUERY_SINCE)" --out "$(QUERY_OUT)"
