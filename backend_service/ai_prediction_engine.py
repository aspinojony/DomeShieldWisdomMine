import time
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
import threading
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from contextlib import asynccontextmanager

# --- 模拟 AI 训练数据生成与单文件封装 ---
# 在真实的系统中，数据来源于长期 InfluxDB 和灾害事件库
print("💽 [AI 中心] 正在初始化“穹盾智矿”预测底座...")
print("⚙️ [AI 中心] 正在加载露井联采历史地质数据集...")

# 伪造 1000 条训练数据 (模拟正常波动 vs 灾害前兆)
np.random.seed(42)
X_normal = np.random.normal(
    loc=[1.5, 20.0, 0.1, 1.0], scale=[0.5, 10.0, 0.05, 0.5], size=(800, 4)
)
y_normal = np.zeros(800)  # Label 0: 正常

X_risk = np.random.normal(
    loc=[15.0, 250.0, 2.5, 15.0], scale=[3.0, 50.0, 0.5, 5.0], size=(200, 4)
)
y_risk = np.ones(200)  # Label 1: 塌方风险

X_train = np.vstack([X_normal, X_risk])
y_train = np.concatenate([y_normal, y_risk])

# 定义核心模型
model = GradientBoostingClassifier(
    n_estimators=100, learning_rate=0.1, max_depth=3, random_state=42
)
print("🧠 [AI 中心] 正在训练风险耦合多模型 (GradientBoostingClassifier)...")
model.fit(X_train, y_train)
print("✅ [AI 中心] 模型训练完成！准确率预估 (模拟): 97.4%")

# --- 阈值引擎 & 虚拟预警库 ---
# 保存最新的警报工单
alert_logs = []


def predict_risk(crack, seismic, angle, settlement):
    """输入: 裂缝(mm), 微震(J), 倾角(°), 沉降(mm)"""
    features = np.array([[crack, seismic, angle, settlement]])
    prob = model.predict_proba(features)[0][1]  # 取塌方概率

    # 按照商业计划书的“三级阶梯式预警逻辑”
    if prob >= 0.85:
        level = "警报级 (三级)"
        action = "🔥 立即派无人机集群核查，发布撤离指令！"
        trigger_uav_dispatch("SLOPE-ZONE-A")  # 触发无人机调度
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


# --- 定时拉取并预测的后台线程 ---
# 真实场景中，你会从 InfluxDB 抽数据。为了 MVP 演示，我们这里读取全局共享内存或者伪造实时流计算
def background_prediction_task():
    device_id = "SLOPE-ZONE-A"
    while True:
        time.sleep(5)  # 每 5 秒推演一次风险

        # 模拟现在矿山传上来的融合传感器数据
        # 正常的时候大概是 [2.0, 15.0, 0.1, 1.2]
        # 有 10% 的概率，地壳剧烈抖动
        is_anomaly = np.random.rand() < 0.1

        if is_anomaly:
            c, se, a, st = 12.5, 180.0, 1.8, 12.0
            print(f"\n🌍 [预警波形] 检测到地层异动！进行 AI 时空推演...")
        else:
            c, se, a, st = 2.0, 15.0, 0.1, 1.2

        prob, level, action = predict_risk(c, se, a, st)

        if prob > 0.2:
            alert_msg = {
                "time": time.strftime("%Y-%m-%d %H:%M:%S"),
                "device": device_id,
                "probability": round(prob * 100, 2),
                "level": level,
                "action": action,
            }
            alert_logs.insert(0, alert_msg)
            # 保持 50 条最新记录
            if len(alert_logs) > 50:
                alert_logs.pop()
            print(
                f"🚨 [智能研判生成] 塌方概率 {prob*100:.1f}%, 级别: {level} -> {action}"
            )


# --- 模拟无人机“机巢”与飞行状态管理 ---
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


def trigger_uav_dispatch(target_zone):
    """当发生严重警报时，分配无人机去目标区域"""
    # 找一台空闲的无人机
    for drone in uav_fleet:
        if drone["status"] == "待命闲置" or drone["status"] == "已返航":
            drone["status"] = "紧急起飞"
            drone["target"] = target_zone
            drone["progress"] = 0
            print(
                f"🚁 [调度中心] 自动工单生成！调派 {drone['id']} 飞往 {target_zone} 执行侦察。"
            )

            # 启动一个独立线程模拟无人机的飞行周期
            threading.Thread(
                target=simulate_drone_flight, args=(drone,), daemon=True
            ).start()
            break


def simulate_drone_flight(drone):
    """模拟无人机飞行：起飞 -> 途中 -> 侦察中 -> 返航 -> 待命"""
    time.sleep(2)
    drone["status"] = "前往目标"
    for p in range(0, 100, 20):
        drone["progress"] = p
        time.sleep(1)

    drone["status"] = "抵近侦察中"
    time.sleep(5)  # 模拟拍摄和 YOLO 推演的时间

    drone["status"] = "返航中"
    for p in range(100, 0, -20):
        drone["progress"] = p
        time.sleep(1)

    drone["status"] = "已返航"
    drone["target"] = None
    drone["progress"] = 0
    print(f"🚁 [调度中心] {drone['id']} 任务结束，已降落补充能源。")


# --- FastAPI 后端接口 ---


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动后台预测线程
    thread = threading.Thread(target=background_prediction_task, daemon=True)
    thread.start()
    yield
    print("AI 引擎关闭。")


app = FastAPI(title="穹盾智矿 - AI 算法推演引擎", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/v1/ai/alerts")
def get_ai_alerts():
    """供前端抓取由 AI 模型推演生成的智能警报工单"""
    return {
        "status": "success",
        "total": len(alert_logs),
        "data": alert_logs[:10],  # 返回最新的 10 条
    }


@app.get("/api/v1/drones/status")
def get_drones_status():
    """供数字孪生大屏拉取实时的无人机舰队状态和坐标进度"""
    return {"status": "success", "data": uav_fleet}


if __name__ == "__main__":
    print("\n==============================================")
    print(" 🚀 [穹盾智矿] 风险耦合多模型融合推演引擎已启动")
    print(" 📡 监听端口: 8001 / API 接口就绪")
    print("==============================================\n")
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="warning")
