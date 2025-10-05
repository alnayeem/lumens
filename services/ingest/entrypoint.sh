#!/bin/sh
set -e

# Build argument list from environment with sensible defaults
CHANNELS="${CHANNELS_CSV:-data/channels/islamic_kids.csv}"
OUT_PREFIX="${OUT_PREFIX:-/tmp/out/videos}"
LIMIT_VAL="${LIMIT:-50}"
INGEST_LANG="${INGEST_LANG:-}"

# Build argv safely without relying on shell parsing
set -- --channels "$CHANNELS" --out "$OUT_PREFIX" --limit "$LIMIT_VAL"
if [ -n "$INGEST_LANG" ]; then
  set -- "$@" --lang "$INGEST_LANG"
fi
if [ -n "${LUMENS_GCP_PROJECT:-}" ]; then
  set -- "$@" --firestore-project "$LUMENS_GCP_PROJECT"
fi

# Execute the ingest CLI
exec python -m services.ingest.cli "$@"
