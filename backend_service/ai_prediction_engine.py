import os
import sys
import time
import numpy as np
import pandas as pd
import threading
import requests
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from contextlib import asynccontextmanager
import torch
import warnings
import datetime
import math

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
latest_vision_result = None  # 存储最近一次无人机侦察的视觉分析结果
force_crisis = False  # 手动触发危机模拟的全局开关

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

        # 随机触发 (保留原本的自然触发逻辑)
        if risk_timer == 0 and np.random.rand() < 0.05:
            risk_timer = 20  # 持续恶化 20 次循环
            t = 0
            print(f"\n🌍 [预警波形] 地质环境开始异动 (发生轻微滑动)...")

        if risk_timer > 0:
            # 模拟逐渐恶化的数据 (加强力度以便触发 85% 门限)
            t_frac = t / 20.0
            new_point = [
                1.5 + 45.0 * t_frac,  # 裂缝
                15 + 1500.0 * (t_frac**2),  # 微震
                0.1 + 8.0 * (t_frac**1.5),  # 倾角
                1.0 + 40.0 * (t_frac**2.5),  # 沉降
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
                "id": f"ALERT-{int(time.time()*1000)}",  # 唯一ID用于前端选中
                "time": time.strftime("%Y-%m-%d %H:%M:%S"),
                "device": device_id,
                "probability": round(prob * 100, 2),
                "level": level,
                "action": action,
                # 证据窗口: 转换回常规列表以便 JSON 序列化
                "evidence": window_array.tolist(),
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

            # --- 联动 8002: 创建工单 ---
            try:
                # 模拟登录获取 token (生产环境应使用专用 service account)
                auth_res = requests.post(
                    "http://127.0.0.1:8002/api/v1/auth/login",
                    data={"username": "admin", "password": "admin123"},
                )
                token = auth_res.json().get("access_token")

                requests.post(
                    "http://127.0.0.1:8002/api/v1/uav/missions",
                    json={
                        "device_id": "UAV-DJI-001",
                        "mission_name": f"AI 自动触发: {target_zone} 风险核查",
                        "waypoints": '[{"lat": 39.63, "lng": 109.84}]',
                    },
                    headers={"Authorization": f"Bearer {token}"},
                )
            except Exception as e:
                print(f"⚠️ [联动] 无法连接业务后台创建工单: {e}")

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

    # --- 联动 8003: 视觉确认 ---
    global latest_vision_result
    print(f"📸 [AI 中心] {drone['id']} 正在回传现场高清图，送交视觉智脑 (8003) 研判...")
    try:
        # 优先使用项目内样例图；没有则回退到最近一次结果图
        candidate_paths = [
            os.path.join(os.path.dirname(__file__), "..", "results", "cv", "detected_1772629371.jpg"),
            os.path.join(os.path.dirname(__file__), "..", "results", "cv", "detected_1772628349.jpg"),
            os.path.join(os.path.dirname(__file__), "..", "results", "cv", "detected_1772627350.jpg"),
        ]
        test_img_path = next((p for p in candidate_paths if os.path.exists(p)), None)
        if not test_img_path:
            raise FileNotFoundError("No bundled UAV sample image found")
        with open(test_img_path, "rb") as f:
            res = requests.post(
                "http://127.0.0.1:8003/api/v1/vision/analyze_crack", files={"file": f}
            )
            latest_vision_result = res.json()
            print(
                f"🔍 [视觉结果] 研判级别: {latest_vision_result.get('data', {}).get('alert_level')}"
            )
    except Exception as e:
        print(f"⚠️ [视觉] 图片研判请求失败: {e}")

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


def get_demo_scene(now=None):
    now = now or datetime.datetime.now()
    cycle = 360
    sec = int(now.timestamp()) % cycle
    if sec < 150:
        phase = 'stable'; progress = sec / 150
    elif sec < 220:
        phase = 'precursor'; progress = (sec - 150) / 70
    elif sec < 280:
        phase = 'warning'; progress = (sec - 220) / 60
    elif sec < 330:
        phase = 'dispatch'; progress = (sec - 280) / 50
    else:
        phase = 'recovery'; progress = (sec - 330) / 30
    return phase, max(0.0, min(1.0, progress)), sec


@app.get("/api/v1/ai/alerts")
def get_ai_alerts():
    now = datetime.datetime.now()
    phase, progress, sec = get_demo_scene(now)
    conf = {
        'stable': (18.0, '安全', '持续监测'),
        'precursor': (42.0, '监控级 (一级)', '提高边坡区域采样频率'),
        'warning': (68.0, '预警级 (二级)', '建议派遣无人机抵近核查'),
        'dispatch': (84.0, '预警级 (二级)', '无人机正在执行视觉复核'),
        'recovery': (46.0, '监控级 (一级)', '现场复核完成，转入持续观察'),
    }
    base_prob, level, action = conf[phase]
    prob = round(base_prob + math.sin(sec / 11) * 2.2 + progress * 3.5, 2)
    item = {'id': f'AI-SCENE-{phase}-{sec}', 'time': now.strftime('%Y-%m-%d %H:%M:%S'), 'device': 'SLOPE-ZONE-A', 'probability': prob, 'level': level, 'action': action, 'evidence': np.zeros((60, 4)).tolist()}
    return {'status': 'success', 'total': 1, 'scene_phase': phase, 'data': [item]}


@app.get("/api/v1/drones/status")
def get_drones_status():
    now = datetime.datetime.now()
    phase, progress, sec = get_demo_scene(now)
    if phase == 'stable':
        fleet = [{'id': 'UAV-EAGLE-01', 'type': '先锋侦察机', 'status': '例行巡检', 'target': '北侧边坡巡检航线', 'progress': int((sec % 150) / 150 * 100)}, {'id': 'UAV-MAPPER-02', 'type': '图传测绘机', 'status': '待命闲置', 'target': None, 'progress': 0}]
    elif phase == 'precursor':
        fleet = [{'id': 'UAV-EAGLE-01', 'type': '先锋侦察机', 'status': '返航待命', 'target': '机库', 'progress': 100}, {'id': 'UAV-MAPPER-02', 'type': '图传测绘机', 'status': '任务预热', 'target': 'SLOPE-ZONE-A', 'progress': 15}]
    elif phase == 'warning':
        fleet = [{'id': 'UAV-EAGLE-01', 'type': '先锋侦察机', 'status': '起飞准备', 'target': 'SLOPE-ZONE-A', 'progress': int(25 + progress * 30)}, {'id': 'UAV-MAPPER-02', 'type': '图传测绘机', 'status': '链路检查', 'target': '北侧坡面', 'progress': int(35 + progress * 20)}]
    elif phase == 'dispatch':
        fleet = [{'id': 'UAV-EAGLE-01', 'type': '先锋侦察机', 'status': '抵近侦察中', 'target': 'SLOPE-ZONE-A', 'progress': int(55 + progress * 35)}, {'id': 'UAV-MAPPER-02', 'type': '图传测绘机', 'status': '图传回传', 'target': 'SLOPE-ZONE-A', 'progress': int(62 + progress * 28)}]
    else:
        fleet = [{'id': 'UAV-EAGLE-01', 'type': '先锋侦察机', 'status': '返航中', 'target': '机库', 'progress': int(85 + progress * 15)}, {'id': 'UAV-MAPPER-02', 'type': '图传测绘机', 'status': '任务结束', 'target': None, 'progress': 100}]
    return {'status': 'success', 'scene_phase': phase, 'data': fleet}


@app.get("/api/v1/vision/latest")
def get_latest_vision():
    now = datetime.datetime.now()
    phase, progress, sec = get_demo_scene(now)
    conf = {
        'stable': ('安全 - 常规巡检未见异常', 2.1),
        'precursor': ('关注 - 坡面局部纹理变化', 2.8),
        'warning': ('二级预警 - 检测到裂缝扩展趋势', 4.3),
        'dispatch': ('二级预警 - 裂缝扩展已复核确认', 5.1),
        'recovery': ('关注 - 裂缝稳定，进入持续观察', 3.6),
    }
    level, width = conf[phase]
    data = {'alert_level': level, 'zone_id': 'SLOPE-ZONE-A', 'image_url': '/results/crack_demo_1.jpg', 'max_width_mm': round(width + math.sin(sec / 10) * 0.15, 1), 'timestamp': now.strftime('%Y-%m-%d %H:%M:%S')}
    return {'status': 'success', 'scene_phase': phase, 'data': data}


@app.post("/api/v1/ai/trigger_crisis")
def trigger_manual_crisis():
    """一键触发危机演练：立即启动全链路联动流程 (演示专用)"""
    global alert_logs

    # 1. 注入一条虚拟的高危预警记录，触发前端大屏红闪和语音播报
    alert_msg = {
        "id": f"ALERT-DEMO-{int(time.time()*1000)}",
        "time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "device": "SLOPE-ZONE-A",
        "probability": 98.74,
        "level": "警报级 (三级)",
        "action": "🔥 立即派无人机集群核查，发布撤离指令！",
        "evidence": np.random.rand(60, 4).tolist(),
    }
    alert_logs.insert(0, alert_msg)

    # 2. 立即触发无人机调度链路 (包含 8002 派单和 8003 视觉辅助)
    trigger_uav_dispatch("SLOPE-ZONE-A")

    print("🚨 [演示中心] 手动触发联动成功：高危预警已注入，无人机已起飞。")
    return {
        "status": "success",
        "message": "🚨 联动演示已启动！检测到高危风险，无人机正在紧急起飞执行视觉确认。",
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="warning")
