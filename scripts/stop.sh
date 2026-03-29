#!/usr/bin/env bash
set -euo pipefail
for port in 5173 8000 8001 8002 8003; do
  pids=$(lsof -tiTCP:"$port" -sTCP:LISTEN || true)
  if [ -n "$pids" ]; then
    echo "[stop] :$port -> $pids"
    kill $pids || true
  else
    echo "[skip] nothing on :$port"
  fi
done
