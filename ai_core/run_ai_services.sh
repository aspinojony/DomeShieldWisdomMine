#!/bin/bash
cd "$(dirname "$0")"

rm -rf venv
python3 -m venv venv

./venv/bin/pip install torch torchvision torchaudio numpy pandas scikit-learn ultralytics fastapi uvicorn python-multipart requests

echo "Starting AI Nodes..."

./venv/bin/python vision_inference_service.py &
PID_VISION=$!

# 时序节点需前往对应的 backend_service 执行引擎调用，所以这里的结构略微不同
# 不过直接通过 `ai_prediction_engine` 在外层拉起即可
cd ../backend_service
./venv/bin/python ai_prediction_engine.py &
PID_TS=$!

echo "AI Engines started: Vision=$PID_VISION, TimeSeries=$PID_TS"
wait
