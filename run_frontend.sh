#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cd "$ROOT_DIR/frontend"
exec python3 -m http.server 3000

#cd /Users/krishna/Documents/NJII-project
# ./run_frontend.sh

# http://127.0.0.1:3000