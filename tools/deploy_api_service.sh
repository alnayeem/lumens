#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Build and deploy the FastAPI web app to Cloud Run (service).

Required:
  -p, --project ID           GCP project (e.g., lumens-alnayeem-dev-02)
  -r, --region NAME          Region (e.g., us-central1)

Optional:
  -R, --repo NAME            Artifact Registry repo (default: lumens)
  -i, --image NAME           Image name (default: api)
  -s, --service NAME         Cloud Run Service name (default: lumens-api)
  -a, --service-account SA   Service Account email for runtime (reads Firestore)
  --allow-unauthenticated    Allow public access (default on)

Notes:
 - Requires: gcloud auth, Artifact Registry, Cloud Build, Cloud Run Admin.
 - App expects env LUMENS_GCP_PROJECT for Firestore reads.

Examples:
  ./tools/deploy_api_service.sh -p $LUMENS_GCP_PROJECT -r us-central1 \
    -a sa-data-runner@${LUMENS_GCP_PROJECT}.iam.gserviceaccount.com
USAGE
}

PROJECT=""
REGION=""
REPO="lumens"
IMAGE="api"
SERVICE="lumens-api"
SA=""
ALLOW_UNAUTH=1

while [[ $# -gt 0 ]]; do
  case "$1" in
    -p|--project) PROJECT="$2"; shift 2;;
    -r|--region) REGION="$2"; shift 2;;
    -R|--repo) REPO="$2"; shift 2;;
    -i|--image) IMAGE="$2"; shift 2;;
    -s|--service) SERVICE="$2"; shift 2;;
    -a|--service-account) SA="$2"; shift 2;;
    --allow-unauthenticated) ALLOW_UNAUTH=1; shift;;
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

# Build and push using the Dockerfile in apps/api
gcloud builds submit apps/api --tag "$IMG_URI"

# Deploy Cloud Run Service
DEPLOY_ARGS=(
  --image "$IMG_URI"
  --region "$REGION"
  --set-env-vars "LUMENS_GCP_PROJECT=$PROJECT"
)
if [[ -n "$SA" ]]; then
  DEPLOY_ARGS+=(--service-account "$SA")
fi
if [[ $ALLOW_UNAUTH -eq 1 ]]; then
  DEPLOY_ARGS+=(--allow-unauthenticated)
fi

gcloud run deploy "$SERVICE" "${DEPLOY_ARGS[@]}"

set +x
echo "Done. Cloud Run Service: $SERVICE in $REGION. Image: $IMG_URI"

