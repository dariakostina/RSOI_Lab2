#!/usr/bin/env bash
set -Eeuxo pipefail

exec /venv/bin/uvicorn "$SERVICE_NAME.main:app"
