#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Build and deploy the ingest Cloud Run Job, and (optionally) create a scheduler.

Required:
  -p, --project ID           GCP project (e.g., lumens-alnayeem-dev-02)
  -r, --region NAME          Region (e.g., us-central1)

Optional:
  -R, --repo NAME            Artifact Registry repo (default: lumens)
  -i, --image NAME           Image name (default: ingest)
  -j, --job NAME             Cloud Run Job name (default: lumens-ingest)
  -s, --service-account SA   Runner SA email (e.g., sa-data-runner@PROJECT.iam.gserviceaccount.com)
  --schedule CRON            If set, creates a Cloud Scheduler HTTP job to trigger the Run Job (e.g., "0 2 * * *")
  --timezone ZONE            Timezone for scheduler (default: UTC)

Notes:
 - Requires: gcloud auth, Cloud Build, Artifact Registry, Cloud Run Admin, Scheduler Admin.
 - Expects Secret Manager secret: lumens-yt-api-key (the YouTube API key)

Examples:
  ./tools/deploy_ingest_job.sh -p $LUMENS_GCP_PROJECT -r us-central1 \
    -s sa-data-runner@${LUMENS_GCP_PROJECT}.iam.gserviceaccount.com \
    --schedule "0 3 * * *"
USAGE
}

PROJECT=""
REGION=""
REPO="lumens"
IMAGE="ingest"
JOB="lumens-ingest"
SA=""
CRON=""
TZ="UTC"

while [[ $# -gt 0 ]]; do
  case "$1" in
    -p|--project) PROJECT="$2"; shift 2;;
    -r|--region) REGION="$2"; shift 2;;
    -R|--repo) REPO="$2"; shift 2;;
    -i|--image) IMAGE="$2"; shift 2;;
    -j|--job) JOB="$2"; shift 2;;
    -s|--service-account) SA="$2"; shift 2;;
    --schedule) CRON="$2"; shift 2;;
    --timezone) TZ="$2"; shift 2;;
    -h|--help) usage; exit 0;;
    *) echo "Unknown arg: $1"; usage; exit 2;;
  esac
done

if [[ -z "$PROJECT" || -z "$REGION" ]]; then
  echo "ERROR: --project and --region are required" >&2
  usage; exit 2
fi

set -x
gcloud config set project "$PROJECT"

# Ensure Artifact Registry repo exists
if ! gcloud artifacts repositories describe "$REPO" --location="$REGION" >/dev/null 2>&1; then
  gcloud artifacts repositories create "$REPO" --repository-format=docker --location="$REGION" --description="Lumens containers"
fi

IMG_URI="$REGION-docker.pkg.dev/$PROJECT/$REPO/$IMAGE:$(date +%Y%m%d-%H%M%S)"

# Build and push via Cloud Build using the root Dockerfile
# Use default Cloud Build logging to avoid custom bucket permission issues.
gcloud builds submit . --tag "$IMG_URI"

# Create or update Cloud Run Job
RUN_ARGS=(
  --image "$IMG_URI"
  --region "$REGION"
  --set-env-vars "LUMENS_GCP_PROJECT=$PROJECT"
  --set-secrets "LUMENS_YT_API_KEY=lumens-yt-api-key:latest"
  --max-retries 1
)
if [[ -n "$SA" ]]; then
  RUN_ARGS+=(--service-account "$SA")
fi

if gcloud run jobs describe "$JOB" --region "$REGION" >/dev/null 2>&1; then
  gcloud run jobs update "$JOB" "${RUN_ARGS[@]}"
else
  gcloud run jobs create "$JOB" "${RUN_ARGS[@]}"
fi

# Optional: schedule via Cloud Scheduler HTTP target
if [[ -n "$CRON" ]]; then
  # Ensure scheduler API is enabled
  gcloud services enable cloudscheduler.googleapis.com
  SCHED_NAME="${JOB}-schedule"
  URL="https://run.googleapis.com/apis/run.googleapis.com/v1/projects/$PROJECT/locations/$REGION/jobs/$JOB:run"
  BODY='{}'
  if gcloud scheduler jobs describe "$SCHED_NAME" --location "$REGION" >/dev/null 2>&1; then
    gcloud scheduler jobs update http "$SCHED_NAME" \
      --location "$REGION" \
      --schedule "$CRON" \
      --time-zone "$TZ" \
      --http-method POST \
      --uri "$URL" \
      --oidc-service-account-email "$SA" \
      --oidc-token-audience "https://run.googleapis.com/"
  else
    gcloud scheduler jobs create http "$SCHED_NAME" \
      --location "$REGION" \
      --schedule "$CRON" \
      --time-zone "$TZ" \
      --http-method POST \
      --uri "$URL" \
      --oidc-service-account-email "$SA" \
      --oidc-token-audience "https://run.googleapis.com/"
  fi
fi

set +x
echo "Done. Cloud Run Job: $JOB in $REGION. Latest image: $IMG_URI"
