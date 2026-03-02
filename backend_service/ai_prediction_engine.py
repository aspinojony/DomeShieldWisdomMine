import os
import sys
import time
import numpy as np
import pandas as pd
import threading
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from contextlib import asynccontextmanager
import torch
import warnings

warnings.filterwarnings("ignore")

# 加载 LSTM 模型相关
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from ai_core.models.ts.multi_modal_lstm import MultiSensorLSTM
from sklearn.preprocessing import StandardScaler

# ==========================================
# 真实 AI 推演引擎初始化 (从空壳 -> 实体模型)
# ==========================================
print("💽 [AI 中心] 正在初始化“穹盾智矿”真实时空预测引擎...")

# 1. 挂载训练好的权重
INPUT_DIM = 4
HIDDEN_DIM = 64
NUM_LAYERS = 2
SEQ_LEN = 60

device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
model = MultiSensorLSTM(
    input_dim=INPUT_DIM, hidden_dim=HIDDEN_DIM, num_layers=NUM_LAYERS, dropout=0
).to(device)
model.eval()

weight_path = os.path.join(
    os.path.dirname(__file__), "../ai_core/checkpoints/MultiSensor_LSTM_V1_best.pt"
)
try:
    model.load_state_dict(torch.load(weight_path, map_location=device))
    print(f"✅ [AI 中心] 成功加载真实物理训练权重: {weight_path}")
except Exception as e:
    print(f"❌ [AI 中心] 权重加载失败, 回退至随机预测模式: {e}")
    model = None

# 2. 拟合预测专用的 Scaler (生产环境应加载保存的 Scaler，这里为了 MVP 快速使用同源数据拟合)
data_path = os.path.join(
    os.path.dirname(__file__), "../ai_core/data/synthetic_sensor_data.csv"
)
scaler = StandardScaler()
try:
    df = pd.read_csv(data_path)
    feature_cols = [
        "crack_width_mm",
        "seismic_energy_j",
        "angle_x_deg",
        "settlement_mm",
    ]
    scaler.fit(df[feature_cols].values)
    print("✅ [AI 中心] 传感器全局归一化拟合模块加载完毕。")
except Exception as e:
    print(f"⚠️ [AI 中心] Scaler 数据加载失败: {e}")

# ==========================================
# 业务状态字典与逻辑分发
# ==========================================
alert_logs = []

uav_fleet = [
    {
        "id": "UAV-EAGLE-01",
        "type": "先锋侦察机",
        "status": "待命闲置",
        "target": None,
        "progress": 0,
    },
    {
        "id": "UAV-MAPPER-02",
        "type": "图传测绘机",
        "status": "待命闲置",
        "target": None,
        "progress": 0,
    },
]

# 模拟一个 60 时序窗口的数据流队列
mock_data_queue = []


def predict_risk_lstm(window_data_2d):
    """
    输入: shape=(60, 4) 的真实传感器数据窗口
    """
    if model is None:
        return np.random.rand(), "安全", "降级"

    # 标准化
    scaled_data = scaler.transform(window_data_2d)

    # 升维 [1, 60, 4] 并转为 Tensor
    x_tensor = torch.tensor(scaled_data, dtype=torch.float32).unsqueeze(0).to(device)

    with torch.no_grad():
        prob = model(x_tensor).item()

    if prob >= 0.85:
        level = "警报级 (三级)"
        action = "🔥 立即派无人机集群核查，发布撤离指令！"
        trigger_uav_dispatch("SLOPE-ZONE-A")
    elif prob >= 0.50:
        level = "预警级 (二级)"
        action = "⚠️ 触发相关管理人员 APP 重点关注！"
    elif prob >= 0.20:
        level = "监控级 (一级)"
        action = "👀 加密下一次无人机巡检网格。"
    else:
        level = "安全"
        action = "✅ 平稳运行中"

    return prob, level, action


def background_prediction_task():
    global mock_data_queue
    device_id = "SLOPE-ZONE-A"

    # 初始化填充 60 个正常帧
    for _ in range(SEQ_LEN):
        mock_data_queue.append(
            [
                np.random.normal(1.5, 0.2),  # crack
                np.random.normal(15, 2.0),  # seismic
                np.random.normal(0.1, 0.02),  # angle
                np.random.normal(1.0, 0.2),  # settlement
            ]
        )

    risk_timer = 0
    t = 0

    while True:
        time.sleep(3)  # 每 3 秒拉取最新实时流切片

        # 为了演示系统，随机触发一段时间的 渐进式塌方前兆
        if risk_timer == 0 and np.random.rand() < 0.05:
            risk_timer = 20  # 持续恶化 20 次循环
            t = 0
            print(f"\\n🌍 [预警波形] 地质环境开始异动 (发生轻微滑动)...")

        if risk_timer > 0:
            # 模拟逐渐恶化的数据
            t_frac = t / 20.0
            new_point = [
                1.5 + 15.0 * t_frac,  # 裂缝增大
                15 + 250.0 * (t_frac**2),  # 微震剧烈
                0.1 + 3.0 * (t_frac**1.5),  # 倾角偏转
                1.0 + 20.0 * (t_frac**2.5),  # 沉降加速
            ]
            t += 1
            risk_timer -= 1
        else:
            new_point = [
                np.random.normal(1.5, 0.2),
                np.random.normal(15, 2.0),
                np.random.normal(0.1, 0.02),
                np.random.normal(1.0, 0.2),
            ]

        mock_data_queue.pop(0)
        mock_data_queue.append(new_point)

        # 将滑动窗口放入真实的 PyTorch 网络中进行 Inference
        window_array = np.array(mock_data_queue)
        prob, level, action = predict_risk_lstm(window_array)

        if prob > 0.2:
            alert_msg = {
                "time": time.strftime("%Y-%m-%d %H:%M:%S"),
                "device": device_id,
                "probability": round(prob * 100, 2),
                "level": level,
                "action": action,
            }
            alert_logs.insert(0, alert_msg)
            if len(alert_logs) > 50:
                alert_logs.pop()
            print(
                f"🧠 [多模融合 LSTM] 坍塌概率 {prob*100:.1f}%, 级别: {level} -> {action}"
            )


def trigger_uav_dispatch(target_zone):
    for drone in uav_fleet:
        if drone["status"] == "待命闲置" or drone["status"] == "已返航":
            drone["status"] = "紧急起飞"
            drone["target"] = target_zone
            drone["progress"] = 0
            print(
                f"🚁 [调度中心] 自动工单生成！调派 {drone['id']} 飞往 {target_zone} 执行侦察。"
            )
            threading.Thread(
                target=simulate_drone_flight, args=(drone,), daemon=True
            ).start()
            break


def simulate_drone_flight(drone):
    time.sleep(2)
    drone["status"] = "前往目标"
    for p in range(0, 100, 20):
        drone["progress"] = p
        time.sleep(1)

    drone["status"] = "抵近侦察中"
    time.sleep(5)

    drone["status"] = "返航中"
    for p in range(100, 0, -20):
        drone["progress"] = p
        time.sleep(1)

    drone["status"] = "已返航"
    drone["target"] = None
    drone["progress"] = 0
    print(f"🚁 [调度中心] {drone['id']} 任务结束，已降落。")


@asynccontextmanager
async def lifespan(app: FastAPI):
    thread = threading.Thread(target=background_prediction_task, daemon=True)
    thread.start()
    yield


app = FastAPI(title="穹盾智矿 - 深度学习时空推演引擎", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/v1/ai/alerts")
def get_ai_alerts():
    return {"status": "success", "total": len(alert_logs), "data": alert_logs[:10]}


@app.get("/api/v1/drones/status")
def get_drones_status():
    return {"status": "success", "data": uav_fleet}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="warning")
