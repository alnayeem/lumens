#!/bin/sh
set -e

PORT_VAL="${PORT:-8080}"

exec uvicorn apps.api.main:app --host 0.0.0.0 --port "$PORT_VAL"

