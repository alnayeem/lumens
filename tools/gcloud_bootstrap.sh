#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Bootstrap a GCP project for Lumens (YouTube ingest).

Required:
  -p, --project-id ID          Globally-unique project ID (e.g., lumens-dev-01)
  -b, --billing-account ID     Billing account ID (run: gcloud beta billing accounts list)

Optional:
  -n, --project-name NAME      Display name (default: Lumens Dev)
  --create-api-key             Attempt to create an API key via CLI

Examples:
  ./tools/gcloud_bootstrap.sh -p lumens-dev-01 -b 000000-AAAAAA-111111 --create-api-key

After creation, you can also create/restrict the API key via Console:
  https://console.cloud.google.com/apis/credentials?project=<PROJECT_ID>
USAGE
}

PROJECT_ID=""
BILLING_ACCOUNT=""
PROJECT_NAME="Lumens Dev"
CREATE_KEY=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    -p|--project-id) PROJECT_ID="$2"; shift 2;;
    -b|--billing-account) BILLING_ACCOUNT="$2"; shift 2;;
    -n|--project-name) PROJECT_NAME="$2"; shift 2;;
    --create-api-key) CREATE_KEY=1; shift;;
    -h|--help) usage; exit 0;;
    *) echo "Unknown arg: $1"; usage; exit 2;;
  esac
done

if [[ -z "$PROJECT_ID" || -z "$BILLING_ACCOUNT" ]]; then
  echo "ERROR: --project-id and --billing-account are required" >&2
  usage; exit 2
fi

if ! command -v gcloud >/dev/null 2>&1; then
  echo "ERROR: gcloud not found. Install Google Cloud SDK first." >&2
  exit 2
fi

echo "==> Checking gcloud auth (you may need to run: gcloud auth login)"
gcloud auth list || true

echo "==> Creating project: $PROJECT_ID ($PROJECT_NAME)"
if gcloud projects describe "$PROJECT_ID" >/dev/null 2>&1; then
  echo "Project already exists: $PROJECT_ID"
else
  gcloud projects create "$PROJECT_ID" --name="$PROJECT_NAME"
fi

echo "==> Linking billing account: $BILLING_ACCOUNT"
if gcloud beta billing projects describe "$PROJECT_ID" --format='value(billingEnabled)' 2>/dev/null | grep -qi true; then
  echo "Billing already linked"
else
  gcloud beta billing projects link "$PROJECT_ID" --billing-account "$BILLING_ACCOUNT"
fi

echo "==> Setting default project"
gcloud config set project "$PROJECT_ID"

echo "==> Enabling required services"
gcloud services enable youtube.googleapis.com apikeys.googleapis.com

if [[ "$CREATE_KEY" -eq 1 ]]; then
  echo "==> Creating restricted API key (YouTube Data API v3)"
  set +e
  if gcloud services api-keys keys --help >/dev/null 2>&1; then
    KEY_NAME=$(gcloud services api-keys keys create \
      --display-name="yt-ingest-dev" \
      --format='value(name)')
    gcloud services api-keys keys update "$KEY_NAME" \
      --api-target=service=youtube.googleapis.com >/dev/null
    API_KEY=$(gcloud services api-keys keys get-key-string "$KEY_NAME" --format='value(keyString)')
  else
    KEY_NAME=$(gcloud services api-keys create \
      --display-name="yt-ingest-dev" \
      --format='value(name)')
    # Restrict to YouTube API where supported
    gcloud services api-keys update "$KEY_NAME" \
      --api-target=service=youtube.googleapis.com >/dev/null || true
    # Best-effort retrieval of key string (not always available)
    API_KEY=$(gcloud services api-keys get-key-string "$KEY_NAME" --format='value(keyString)' 2>/dev/null || true)
  fi
  set -e
  echo "Created key resource: $KEY_NAME"
  if [[ -n "${API_KEY:-}" ]]; then
    echo "API key: $API_KEY"
    echo "Export with: export LUMENS_YT_API_KEY=$API_KEY"
  else
    echo "NOTE: Could not read key string via CLI. Retrieve from Console:"
    echo "  https://console.cloud.google.com/apis/credentials?project=$PROJECT_ID"
  fi
else
  echo "==> Skipping API key creation. Create one here and restrict to YouTube Data API v3:"
  echo "  https://console.cloud.google.com/apis/credentials?project=$PROJECT_ID"
fi

echo "==> Done. Next:"
echo "  export LUMENS_YT_API_KEY=..."
echo "  python services/ingest/yt_ingest.py --channels data/channels/islamic_kids.csv --out out/islamic_kids --limit 100"

