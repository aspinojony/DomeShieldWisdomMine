import cv2
import numpy as np
import os
import time
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
import uvicorn
from contextlib import asynccontextmanager

from models.cv.crack_yolo_model import CrackDetectorYOLO

# 全局存储引擎
cv_engine = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global cv_engine
    print("========================================")
    print(" 🚁 [空中侦察节点] 部署无人机视觉推演边缘服务")
    print("========================================")
    # 初始化视觉引擎 (会加载 pt 权重)
    # 为了演示，此处直接调用预先写好的框架 (它第一次启动会从 ultralytics 下载通用的 COCO yolov8n.pt 等模型)
    # 实际项目中，你会将 yolov8n.pt 替换为您自己 train 出的 crack_yolov8_best.pt
    cv_engine = CrackDetectorYOLO(
        config_path="/Users/a0000/天空一体矿山系统/ai_core/configs/cv_yolo.yaml"
    )
    yield
    print("🚁 [视觉节点] 关闭。")


app = FastAPI(title="云边协同 - UAV 图像 AI 分析", lifespan=lifespan)


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
    result = cv_engine.infer(image, conf_threshold=0.25)  # 低置信度以召回更多模糊裂缝
    cost_ms = int((time.time() - start_t) * 1000)

    # 3. 解析目标的 Bounding Boxes
    boxes = result.boxes
    detections = []

    max_crack_width_pixels = 0
    cracks_count = len(boxes)

    # 对每条发现的裂纹分别打包结果
    for box in boxes:
        # 边界框坐标：[左上方x, 左上方y, 右下方x, 右下方y]
        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
        conf = float(box.conf[0])
        cls_int = int(box.cls[0])
        class_name = result.names[cls_int]

        # 假定此处我们只记录了 'crack' 类
        # 计算框的特征宽幅
        width = x2 - x1
        height = y2 - y1
        current_max = min(width, height)  # 裂缝短的那个边才是"宽度"
        if current_max > max_crack_width_pixels:
            max_crack_width_pixels = current_max

        detections.append(
            {
                "label": "crack_anomaly",  # 真实环境由 class_name 决定
                "confidence": f"{conf:.2f}",
                "box": [round(x1, 1), round(y1, 1), round(x2, 1), round(y2, 1)],
            }
        )

        # 使用 OpenCV 在图上画框供展示保存
        color = (0, 0, 255)  # BGR 红框告警
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

    # 4. 落地保存告警佐证图供数字孪生大屏调取
    save_dir = "./results/cv"
    os.makedirs(save_dir, exist_ok=True)
    filename = f"detected_{int(time.time())}.jpg"
    final_save_path = os.path.join(save_dir, filename)
    cv2.imwrite(final_save_path, image)

    # 5. 生成物理学结论（像素转物理尺度的算法，这里用写死的比例尺系数模拟）
    # 比如在焦距 50mm，航高 100m 下， 1像素 ≈ 5毫米
    pixel_to_mm_ratio = 5.0
    max_crack_width_mm = max_crack_width_pixels * pixel_to_mm_ratio

    # 决定警报级别
    level = "安全"
    if max_crack_width_mm > 50:
        level = "警报级 (三级)"
    elif max_crack_width_mm > 20:
        level = "预警级 (二级)"
    elif max_crack_width_mm > 5:
        level = "监控级 (一级)"

    print(
        f"👀 [视觉结果] 发现 {cracks_count} 处裂隙. 最大宽度: {max_crack_width_mm:.1f} mm. 耗时: {cost_ms}ms"
    )

    return {
        "status": "success",
        "data": {
            "processing_time_ms": cost_ms,
            "anomalies_found": cracks_count,
            "max_width_mm": round(max_crack_width_mm, 2),
            "alert_level": level,
            "image_url": f"/static/cv_results/{filename}",
            "details": detections,
        },
    }


if __name__ == "__main__":
    print("▶️ 开始启动空天视觉处理网关...")
    uvicorn.run(app, host="0.0.0.0", port=8002)
