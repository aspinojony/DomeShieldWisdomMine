#!/usr/bin/env bash
set -euo pipefail
for url in \
  http://127.0.0.1:5173/ \
  http://127.0.0.1:8000/health \
  http://127.0.0.1:8001/api/v1/vision/latest \
  http://127.0.0.1:8002/docs \
  http://127.0.0.1:8003/api/v1/vision/latest
 do
  code=$(curl -s -o /dev/null -w "%{http_code}" "$url" || true)
  echo "$code  $url"
 done
