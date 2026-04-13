#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

exec "$ROOT_DIR/backend/venv/bin/python" -m pytest "$ROOT_DIR/backend/tests" "$@"
