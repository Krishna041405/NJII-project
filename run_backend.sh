#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ -f "$ROOT_DIR/.env.supabase" ]; then
    # shellcheck disable=SC1091
    source "$ROOT_DIR/.env.supabase"
fi

cd "$ROOT_DIR/backend"
exec "$ROOT_DIR/backend/venv/bin/python" -m uvicorn app:app --reload

# cd /Users/krishna/Documents/NJII-project
# ./run_backend.sh

