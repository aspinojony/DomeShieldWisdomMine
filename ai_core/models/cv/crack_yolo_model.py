import os
import yaml
from ultralytics import YOLO


class CrackDetectorYOLO:
    """
    针对矿山裂缝与地表形变的定制 YOLOv8 模型包装器。
    用于对接无人机回传的图像进行目标检测。
    """

    def __init__(self, config_path="./configs/cv_yolo.yaml"):
        # 读取超参数配置
        try:
            with open(config_path, "r") as f:
                self.config = yaml.safe_load(f)
        except Exception as e:
            raise RuntimeError(f"加载 YOLO 配置文件失败, 请检查路径: {e}")

        # 将相对路径统一解析到 config 文件目录下
        self.config_dir = os.path.dirname(os.path.abspath(config_path))

        model_cfg = self.config.get("model", {})
        infer_cfg = self.config.get("inference", {})

        # 1) 优先加载同学训练好的权重
        weights_path = (model_cfg.get("weights_path") or "").strip()
        resolved_weights = None
        if weights_path:
            resolved_weights = (
                weights_path
                if os.path.isabs(weights_path)
                else os.path.normpath(os.path.join(self.config_dir, weights_path))
            )
            if not os.path.exists(resolved_weights):
                print(f"⚠️ 指定的 weights_path 不存在: {resolved_weights}，将回退到 model.type")
                resolved_weights = None

        # 2) 回退到基础模型（yolov8n.pt 等）
        model_type = model_cfg.get("type", "yolov8n.pt")
        if resolved_weights:
            model_source = resolved_weights
            print(f"👁 [YOLO 视觉中枢] 加载训练权重: {model_source}")
        else:
            model_source = model_type
            print(f"👁 [YOLO 视觉中枢] 未配置训练权重，加载基础模型: {model_source}")

        self.model = YOLO(model_source)

        # 推理参数
        self.default_conf = float(infer_cfg.get("conf_threshold", 0.25))
        self.default_iou = float(infer_cfg.get("iou_threshold", 0.45))
        self.default_imgsz = int(infer_cfg.get("imgsz", 960))

        # 设备选择兜底：ultralytics 不接受 device="auto"
        req_device = str(infer_cfg.get("device", "auto")).lower().strip()
        if req_device == "auto":
            try:
                import torch
                if torch.cuda.is_available():
                    self.default_device = 0
                elif getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
                    self.default_device = "mps"
                else:
                    self.default_device = "cpu"
            except Exception:
                self.default_device = "cpu"
        else:
            self.default_device = infer_cfg.get("device", "cpu")

    def train(self):
        """执行模型训练 (在拥有标准标注库的情况下)"""
        train_cfg = self.config["training"]
        dataset_cfg = self.config["dataset"]["yaml_path"]

        # 训练数据路径也基于配置文件目录解析
        if not os.path.isabs(dataset_cfg):
            dataset_cfg = os.path.normpath(os.path.join(self.config_dir, dataset_cfg))

        print("🚀 [YOLO 视觉中枢] 开启训练管线...")
        results = self.model.train(
            data=dataset_cfg,
            epochs=train_cfg["epochs"],
            imgsz=train_cfg["imgsz"],
            batch=train_cfg["batch_size"],
            device=train_cfg["device"],
            workers=train_cfg["workers"],
            project=train_cfg["project"],
            name=train_cfg["name"],
        )
        return results

    def infer(self, source_image, conf_threshold=None):
        """
        进行推理解析，用于线上实时识别
        :param source_image: NumPy 数组或图片路径
        """
        conf = self.default_conf if conf_threshold is None else float(conf_threshold)

        results = self.model.predict(
            source=source_image,
            conf=conf,
            iou=self.default_iou,
            imgsz=self.default_imgsz,
            device=self.default_device,
            save=False,  # 不走它默认的 save，我们自己做
            verbose=False,  # 屏蔽内部杂乱输出
        )
        return results[0]  # YOLOv8 支持 batch，这里我们一张张做推理，取第一张图的结果


if __name__ == "__main__":
    # 测试能否成功构建
    detector = CrackDetectorYOLO()
    print("✅ 矿山裂缝视觉检测底座加载成功。")
