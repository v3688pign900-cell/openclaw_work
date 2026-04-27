#!/usr/bin/env bash
set -euo pipefail

PORT="18789"

if lsof -nP -iTCP:"$PORT" -sTCP:LISTEN >/dev/null 2>&1; then
  echo "LISTEN: tcp port $PORT"
  exit 0
else
  echo "NOT LISTEN: tcp port $PORT"
  exit 1
fi
