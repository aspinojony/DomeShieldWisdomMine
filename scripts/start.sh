#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LOG_DIR="/tmp/tiankong-system"
mkdir -p "$LOG_DIR"

start_if_free() {
  local port="$1"
  local name="$2"
  local cmd="$3"
  if lsof -nP -iTCP:"$port" -sTCP:LISTEN >/dev/null 2>&1; then
    echo "[skip] $name already listening on :$port"
  else
    echo "[start] $name -> :$port"
    bash -lc "cd '$ROOT' && nohup $cmd > '$LOG_DIR/$name.log' 2>&1 &"
    sleep 1
  fi
}

start_if_free 8002 business_api "./backend_service/venv/bin/uvicorn backend_service.business_api:app --host 127.0.0.1 --port 8002"
start_if_free 8000 sensor_api "DEMO_MODE=4{DEMO_MODE:-true} ./backend_service/venv/bin/python backend_service/api_server.py"
start_if_free 8001 ai_engine "./venv/bin/python backend_service/ai_prediction_engine.py"
start_if_free 8003 vision_api "./venv/bin/python ai_core/vision_inference_service.py"
start_if_free 5173 frontend "cd frontend_dashboard && npm run dev -- --host 127.0.0.1"

echo
echo "Frontend: http://127.0.0.1:5173"
echo "Business API: http://127.0.0.1:8002/docs"
echo "Sensor API: http://127.0.0.1:8000/health"
