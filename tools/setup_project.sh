#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
End-to-end setup for a new Lumens dev project on GCP.

Creates/links the project (optional), enables APIs, creates Artifact Registry,
boots Firestore (Native), sets indexes, creates a runner service account,
optionally creates the YouTube API key secret, deploys the ingest Cloud Run Job,
and (optionally) schedules it via Cloud Scheduler.

Required:
  -p, --project-id ID           Target GCP project id
  -r, --region REGION           Region (e.g., us-central1)

Optional:
  -b, --billing-account ID      Billing account (only for --create-project)
  --create-project              Create the project and link billing
  --firestore-location REGION   Firestore region (default: us-central1)
  --repo NAME                   Artifact Registry repo (default: lumens)
  --sa-runner EMAIL|NAME        Runner SA (default: sa-data-runner@PROJECT)
  --yt-api-key-file PATH        File with YouTube API key to create secret lumens-yt-api-key
  --schedule CRON               Create Scheduler (e.g., "0 3 * * *"); requires --sa-runner
  --timezone ZONE               Scheduler timezone (default: UTC)

Examples:
  ./tools/setup_project.sh -p lumens-alnayeem-dev-03 -r us-central1 \
    -b 000000-AAAAAA-111111 --create-project --yt-api-key-file ./yt.key --schedule "0 3 * * *"
USAGE
}

PROJECT_ID=""
REGION=""
BILLING=""
CREATE_PROJECT=0
FS_LOCATION="us-central1"
REPO="lumens"
SA_RUNNER=""
YT_KEY_FILE=""
CRON=""
TZ="UTC"

while [[ $# -gt 0 ]]; do
  case "$1" in
    -p|--project-id) PROJECT_ID="$2"; shift 2;;
    -r|--region) REGION="$2"; shift 2;;
    -b|--billing-account) BILLING="$2"; shift 2;;
    --create-project) CREATE_PROJECT=1; shift;;
    --firestore-location) FS_LOCATION="$2"; shift 2;;
    --repo) REPO="$2"; shift 2;;
    --sa-runner) SA_RUNNER="$2"; shift 2;;
    --yt-api-key-file) YT_KEY_FILE="$2"; shift 2;;
    --schedule) CRON="$2"; shift 2;;
    --timezone) TZ="$2"; shift 2;;
    -h|--help) usage; exit 0;;
    *) echo "Unknown arg: $1"; usage; exit 2;;
  esac
done

if [[ -z "$PROJECT_ID" || -z "$REGION" ]]; then
  echo "ERROR: --project-id and --region are required" >&2
  usage; exit 2
fi

set -x

# Create project (optional) and link billing
if [[ $CREATE_PROJECT -eq 1 ]]; then
  if [[ -z "$BILLING" ]]; then
    echo "ERROR: --billing-account is required with --create-project" >&2
    exit 2
  fi
  if gcloud projects describe "$PROJECT_ID" >/dev/null 2>&1; then
    echo "Project exists: $PROJECT_ID"
  else
    gcloud projects create "$PROJECT_ID" --name="$PROJECT_ID"
  fi
  gcloud beta billing projects link "$PROJECT_ID" --billing-account "$BILLING" || true
fi

gcloud config set project "$PROJECT_ID"

# Enable core APIs
gcloud services enable \
  run.googleapis.com \
  cloudscheduler.googleapis.com \
  secretmanager.googleapis.com \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com \
  firestore.googleapis.com \
  apikeys.googleapis.com \
  youtube.googleapis.com || true

# Artifact Registry repo
if ! gcloud artifacts repositories describe "$REPO" --location="$REGION" >/dev/null 2>&1; then
  gcloud artifacts repositories create "$REPO" --repository-format=docker --location="$REGION" --description="Lumens containers"
fi

# Firestore (Native)
if gcloud firestore databases describe --project "$PROJECT_ID" >/dev/null 2>&1; then
  echo "Firestore DB exists in $PROJECT_ID"
else
  gcloud firestore databases create --location="$FS_LOCATION" --project "$PROJECT_ID"
fi

# Indexes
bash "$(dirname "$0")/firestore_indexes.sh" -p "$PROJECT_ID"

# Runner SA
if [[ -z "$SA_RUNNER" ]]; then
  SA_RUNNER="sa-data-runner@${PROJECT_ID}.iam.gserviceaccount.com"
fi
if [[ "$SA_RUNNER" != *"@"* ]]; then
  SA_RUNNER="${SA_RUNNER}@${PROJECT_ID}.iam.gserviceaccount.com"
fi
gcloud iam service-accounts create "${SA_RUNNER%%@*}" --display-name="Lumens Ingest Runner" --project "$PROJECT_ID" || true
gcloud projects add-iam-policy-binding "$PROJECT_ID" --member="serviceAccount:$SA_RUNNER" --role="roles/run.developer" || true
gcloud projects add-iam-policy-binding "$PROJECT_ID" --member="serviceAccount:$SA_RUNNER" --role="roles/secretmanager.secretAccessor" || true
gcloud projects add-iam-policy-binding "$PROJECT_ID" --member="serviceAccount:$SA_RUNNER" --role="roles/artifactregistry.reader" || true

# Secret for YT API key (optional)
if [[ -n "$YT_KEY_FILE" ]]; then
  if gcloud secrets describe lumens-yt-api-key --project "$PROJECT_ID" >/dev/null 2>&1; then
    gcloud secrets versions add lumens-yt-api-key --data-file="$YT_KEY_FILE" --project "$PROJECT_ID"
  else
    gcloud secrets create lumens-yt-api-key --data-file="$YT_KEY_FILE" --project "$PROJECT_ID"
  fi
else
  echo "(info) Skipping YT API key secret creation; provide --yt-api-key-file to create/update lumens-yt-api-key"
fi

# Deploy job image and Cloud Run Job (and schedule if requested)
bash "$(dirname "$0")/deploy_ingest_job.sh" -p "$PROJECT_ID" -r "$REGION" -R "$REPO" -i ingest -j lumens-ingest -s "$SA_RUNNER" ${CRON:+ --schedule "$CRON"} ${TZ:+ --timezone "$TZ"}

set +x
echo "Done. Project $PROJECT_ID is set up. Runner SA: $SA_RUNNER"
