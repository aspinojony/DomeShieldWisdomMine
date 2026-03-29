#!/bin/bash
cd "$(dirname "$0")"

# 强行销毁重建 venv
rm -rf venv
python3 -m venv venv

# 使用绝对路径的 pip 确保安装到虚拟环境中
./venv/bin/pip install fastapi uvicorn sqlalchemy paho-mqtt influxdb-client kafka-python "python-jose[cryptography]" passlib bcrypt pandas numpy scikit-learn python-multipart

echo "Dependencies installed, starting services..."

# 启动数据摄取网关
./venv/bin/python data_ingestion.py &
PID_INGESTION=$!

# 启动时序历史网关
./venv/bin/uvicorn api_server:app --host 0.0.0.0 --port 8000 &
PID_API=$!

# 启动鉴权验证业务网关
./venv/bin/uvicorn business_api:app --host 0.0.0.0 --port 8002 &
PID_BUSINESS=$!

echo "All backend services started."
echo "PIDs: Ingestion=$PID_INGESTION, API=$PID_API, Business=$PID_BUSINESS"

wait
