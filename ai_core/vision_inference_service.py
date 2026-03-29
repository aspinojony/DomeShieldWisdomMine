import cv2
import numpy as np
import os
import time
import json
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
from contextlib import asynccontextmanager

from models.cv.crack_yolo_model import CrackDetectorYOLO

# 全局存储引擎
cv_engine = None
HISTORY_FILE = "./results/cv/history.json"


def save_history(entry):
    history = []
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                history = json.load(f)
        except:
            history = []

    history.insert(0, entry)  # 最新在最前
    # 仅保留最近 100 条
    history = history[:100]

    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


@asynccontextmanager
async def lifespan(app: FastAPI):
    global cv_engine
    print("========================================")
    print(" 🚁 [空中侦察节点] 部署无人机视觉推演边缘服务")
    print("========================================")
    # 确保目录存在
    os.makedirs("./results/cv", exist_ok=True)
    if not os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump([], f)

    # 初始化视觉引擎
    cv_engine = CrackDetectorYOLO(
        config_path="/Users/a0000/天空一体矿山系统/ai_core/configs/cv_yolo.yaml"
    )
    yield
    print("🚁 [视觉节点] 关闭。")


app = FastAPI(title="云边协同 - UAV 图像 AI 分析", lifespan=lifespan)

# 挂载静态资源目录
app.mount("/static/cv_results", StaticFiles(directory="./results/cv"), name="static")


@app.get("/api/v1/vision/history")
async def get_vision_history():
    """获取历史分析记录"""
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


@app.get("/api/v1/vision/latest")
async def get_latest_vision():
    """获取最新的一条分析记录"""
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            history = json.load(f)
            if history:
                return history[0]
    return None


@app.post("/api/v1/vision/analyze_crack")
async def analyze_crack(file: UploadFile = File(...)):
    """
    接收来自无人机侦察回传的高清图像，进行多尺度裂缝特征识别并框定告警。
    """
    if not cv_engine:
        return {"error": "视觉引擎尚未就绪。"}

    # 1. 解析客户端推过的图片二进制流
    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if image is None:
        return JSONResponse(status_code=400, content={"error": "图片流解析失败"})

    # 2. 将图片丢入 YOLO 推演信道
    print(
        f"📡 [云脑接收] 收到侦察图片 ({image.shape[1]}x{image.shape[0]}), 送入 YOLO 分析管线..."
    )

    start_t = time.time()
    result = cv_engine.infer(image, conf_threshold=0.25)
    cost_ms = int((time.time() - start_t) * 1000)

    # 3. 解析目标的 Bounding Boxes
    boxes = result.boxes
    detections = []

    max_crack_width_pixels = 0
    cracks_count = len(boxes)

    for box in boxes:
        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
        conf = float(box.conf[0])
        cls_int = int(box.cls[0])

        width = x2 - x1
        height = y2 - y1
        current_max = min(width, height)
        if current_max > max_crack_width_pixels:
            max_crack_width_pixels = current_max

        detections.append(
            {
                "label": "crack_anomaly",
                "confidence": f"{conf:.2f}",
                "box": [
                    round(float(x1), 1),
                    round(float(y1), 1),
                    round(float(x2), 1),
                    round(float(x2), 1),
                ],
            }
        )

        color = (0, 0, 255)
        cv2.rectangle(image, (int(x1), int(y1)), (int(x2), int(y2)), color, 2)
        text = f"CRACK {conf*100:.1f}%"
        cv2.putText(
            image,
            text,
            (int(x1), int(y1) - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            color,
            2,
        )

    # 4. 落地保存告警佐证图
    filename = f"detected_{int(time.time())}_{cracks_count}.jpg"
    final_save_path = os.path.join("./results/cv", filename)
    cv2.imwrite(final_save_path, image)

    # 5. 生成物理学结论
    pixel_to_mm_ratio = 5.0
    max_crack_width_mm = max_crack_width_pixels * pixel_to_mm_ratio

    level = "安全"
    if max_crack_width_mm > 50:
        level = "警报级 (三级)"
    elif max_crack_width_mm > 20:
        level = "预警级 (二级)"
    elif max_crack_width_mm > 5:
        level = "监控级 (一级)"

    result_data = {
        "id": f"VID_{int(time.time())}",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "processing_time_ms": cost_ms,
        "anomalies_found": cracks_count,
        "max_width_mm": round(float(max_crack_width_mm), 2),
        "alert_level": level,
        "image_url": f"/static/cv_results/{filename}",
        "details": detections,
    }

    # 持久化到历史记录
    save_history(result_data)

    print(
        f"👀 [视觉结果] 发现 {cracks_count} 处裂隙. 最大宽度: {max_crack_width_mm:.1f} mm. 耗时: {cost_ms}ms"
    )

    return {
        "status": "success",
        "data": result_data,
    }


if __name__ == "__main__":
    from datetime import datetime

    print("▶️ 开始启动空天视觉处理网关...")
    uvicorn.run(app, host="0.0.0.0", port=8003)
