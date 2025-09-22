#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Create recommended Firestore composite indexes for the Lumens content collection.

Required:
  -p, --project ID                GCP project id (e.g., lumens-alnayeem-dev-02)

Optional:
  -g, --group NAME                Collection group (default: content)
  --dry-run                       Print commands without executing

Examples:
  ./tools/firestore_indexes.sh -p lumens-alnayeem-dev-02
  ./tools/firestore_indexes.sh -p $LUMENS_GCP_PROJECT --dry-run
USAGE
}

PROJECT=""
GROUP="content"
DRYRUN=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    -p|--project) PROJECT="$2"; shift 2;;
    -g|--group) GROUP="$2"; shift 2;;
    --dry-run) DRYRUN=1; shift;;
    -h|--help) usage; exit 0;;
    *) echo "Unknown arg: $1"; usage; exit 2;;
  esac
done

if [[ -z "${PROJECT}" ]]; then
  echo "ERROR: --project is required" >&2
  usage
  exit 2
fi

cmd() {
  if [[ $DRYRUN -eq 1 ]]; then
    echo "DRYRUN> $*"
  else
    eval "$@"
  fi
}

create_index() {
  local args="$1"
  set +e
  cmd gcloud firestore indexes composite create --collection-group="${GROUP}" ${args} --project "${PROJECT}"
  local rc=$?
  set -e
  if [[ $rc -ne 0 ]]; then
    echo "(skip) create failed or exists: gcloud firestore indexes composite create ${args}"
  fi
}

echo "==> Creating Firestore indexes for project=${PROJECT}, group=${GROUP}"

# 1) language + published_at DESC
create_index "--field-config field-path=language,order=ASCENDING --field-config field-path=published_at,order=DESCENDING"

# 2) channel_id + published_at DESC
create_index "--field-config field-path=channel_id,order=ASCENDING --field-config field-path=published_at,order=DESCENDING"

# 3) made_for_kids + published_at DESC
create_index "--field-config field-path=made_for_kids,order=ASCENDING --field-config field-path=published_at,order=DESCENDING"

# 4) topics ARRAY_CONTAINS + published_at DESC
create_index "--field-config field-path=topics,array-config=CONTAINS --field-config field-path=published_at,order=DESCENDING"

echo "==> Submitted index creations. Build time is typically 1–5 minutes."

