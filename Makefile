.PHONY: help venv test ingest ingest-no-enrich install-dev install-ingest ingest-fs install-all resolve-channels ingest-cached query setup-indexes deploy-ingest schedule-ingest setup-project deploy-api wipe-content

CHANNELS?=data/channels/islamic_kids.csv
OUT?=out/islamic_kids
LIMIT?=25

# Select Python/pip executable (override with: make PY=python)
# Prefer repo-local virtualenv if present
PY?=$(if $(wildcard .venv/bin/python),.venv/bin/python,python3)
# API server port (override with: make run-api PORT=8001)
PORT?=8000
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
	@echo "  run-api             Run the FastAPI web app (reads Firestore, serves HTML on /)"
	@echo "  setup-indexes       Create recommended Firestore composite indexes"
	@echo "  deploy-ingest       Build and deploy Cloud Run Job for ingest"
	@echo "  schedule-ingest     Create/Update Cloud Scheduler job to trigger ingest job"
	@echo "  deploy-api          Build and deploy Cloud Run Service for web API"
	@echo "  wipe-content        DANGER: Delete all docs in Firestore collection (default: content)"
	@echo "  setup-project       One-shot project setup (APIs, Firestore, indexes, SA, job, scheduler)"
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

run-api:
	@if [ -z "$$LUMENS_GCP_PROJECT" ]; then echo "Set LUMENS_GCP_PROJECT to your GCP project id"; exit 2; fi
	$(PY) -m uvicorn apps.api.main:app --reload --port $(PORT)

setup-indexes:
	@if [ -z "$$LUMENS_GCP_PROJECT" ]; then echo "Set LUMENS_GCP_PROJECT to your GCP project id"; exit 2; fi
	bash ./tools/firestore_indexes.sh -p $$LUMENS_GCP_PROJECT

# Deployment helpers
REGION?=us-central1
REPO?=lumens
JOB?=lumens-ingest
SA_EMAIL?=sa-data-runner@$(LUMENS_GCP_PROJECT).iam.gserviceaccount.com
CRON?=0 3 * * *
TZ?=UTC
SERVICE?=lumens-api

deploy-ingest:
	@if [ -z "$$LUMENS_GCP_PROJECT" ]; then echo "Set LUMENS_GCP_PROJECT"; exit 2; fi
	bash ./tools/deploy_ingest_job.sh -p $$LUMENS_GCP_PROJECT -r $(REGION) -R $(REPO) -i ingest -j $(JOB) -s $(SA_EMAIL)

schedule-ingest:
	@if [ -z "$$LUMENS_GCP_PROJECT" ]; then echo "Set LUMENS_GCP_PROJECT"; exit 2; fi
	bash ./tools/deploy_ingest_job.sh -p $$LUMENS_GCP_PROJECT -r $(REGION) -R $(REPO) -i ingest -j $(JOB) -s $(SA_EMAIL) --schedule "$(CRON)" --timezone $(TZ)

setup-project:
	@if [ -z "$(PROJECT_ID)" ]; then echo "Pass PROJECT_ID=... BILLING_ACCOUNT=... REGION=..."; exit 2; fi
	bash ./tools/setup_project.sh -p $(PROJECT_ID) -r $(REGION) $(if $(BILLING_ACCOUNT),-b $(BILLING_ACCOUNT)) $(if $(CREATE_PROJECT),--create-project) $(if $(FIRESTORE_LOCATION),--firestore-location $(FIRESTORE_LOCATION)) $(if $(REPO),--repo $(REPO)) $(if $(SA_EMAIL),--sa-runner $(SA_EMAIL)) $(if $(YT_KEY_FILE),--yt-api-key-file $(YT_KEY_FILE)) $(if $(CRON),--schedule "$(CRON)") $(if $(TZ),--timezone $(TZ))

deploy-api:
	@if [ -z "$$LUMENS_GCP_PROJECT" ]; then echo "Set LUMENS_GCP_PROJECT"; exit 2; fi
	bash ./tools/deploy_api_service.sh -p $$LUMENS_GCP_PROJECT -r $(REGION) -R $(REPO) -i api -s $(SERVICE) -a $(SA_EMAIL)

WIPE_COLLECTION?=content
WIPE_PAGE_SIZE?=500

wipe-content:
	@if [ -z "$$LUMENS_GCP_PROJECT" ]; then echo "Set LUMENS_GCP_PROJECT"; exit 2; fi
	@echo "WARNING: This will delete all documents in collection '$(WIPE_COLLECTION)' in project '$$LUMENS_GCP_PROJECT'."
	@echo "To proceed non-interactively, re-run with YES=1."
	@if [ "$(YES)" = "1" ]; then \
		$(PY) tools/firestore_wipe.py --project $$LUMENS_GCP_PROJECT --collection $(WIPE_COLLECTION) --page-size $(WIPE_PAGE_SIZE) --yes ; \
	else \
		$(PY) tools/firestore_wipe.py --project $$LUMENS_GCP_PROJECT --collection $(WIPE_COLLECTION) --page-size $(WIPE_PAGE_SIZE) ; \
	fi
