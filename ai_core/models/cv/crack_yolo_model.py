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

        # 加载 Ultralytics 模型骨架
        self.model_type = self.config["model"]["type"]
        print(f"👁 [YOLO 视觉中枢] 正在加载轻量级无人机视觉模型引擎: {self.model_type}")
        self.model = YOLO(self.model_type)  # 首次运行会自动从 GitHub 下载权重

    def train(self):
        """执行模型训练 (在拥有标准标注库的情况下)"""
        train_cfg = self.config["training"]
        dataset_cfg = self.config["dataset"]["yaml_path"]

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

    def infer(self, source_image, conf_threshold=0.25):
        """
        进行推理解析，用于线上实时识别
        :param source_image: NumPy 数组或图片路径
        """
        # 返回原生 Results 对象
        results = self.model.predict(
            source=source_image,
            conf=conf_threshold,
            save=False,  # 不走它默认的 save，我们自己做
            verbose=False,  # 屏蔽内部杂乱输出
        )
        return results[0]  # YOLOv8 支持 batch，这里我们一张张做推理，取第一张图的结果


if __name__ == "__main__":
    # 测试能否成功构建
    detector = CrackDetectorYOLO()
    print("✅ 矿山裂缝视觉检测底座加载成功。")
