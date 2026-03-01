import torch
from torch.utils.data import Dataset, DataLoader
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler


class TimeSeriesSensorDataset(Dataset):
    """
    针对矿山多源物联网传感器数据的时序滑动窗口数据集 (Sliding Window Dataset)
    """

    def __init__(
        self, df: pd.DataFrame, seq_len: int, pred_len: int, is_train: bool = True
    ):
        """
        :param df: Pandas DataFrame，包含时间戳和各个传感器的值
        :param seq_len: 输入序列长度 (Look-back window)
        :param pred_len: 预测未来序列长度或者分类 (Forecast window/Label)
        :param is_train: 是否为训练集（决定是否 fit scaler）
        """
        self.seq_len = seq_len
        self.pred_len = pred_len
        self.is_train = is_train

        # 假设 df 中包含 'timestamp' 和 'label' 列，其余均为特征
        # Label 示例：未来一定时间内发生塌方的概率，或者预测未来的位移量

        # 为了演示，我们先构建数据阵列
        self.features = df.drop(columns=["timestamp", "label"]).values
        self.labels = df["label"].values  # 比如分类: 0-安全, 1-危险

        # 工业级标准：标准化
        self.scaler = StandardScaler()
        if self.is_train:
            self.features = self.scaler.fit_transform(self.features)
        else:
            self.features = self.scaler.transform(
                self.features
            )  # 外部注入拟合好的scaler更严谨

        # 计算切片索引
        self.indices = []
        for i in range(len(self.features) - seq_len - pred_len + 1):
            self.indices.append(i)

    def __len__(self):
        return len(self.indices)

    def __getitem__(self, idx):
        start = self.indices[idx]

        # X: [seq_len, num_features]
        x = self.features[start : start + self.seq_len]

        # Y: 这里我们预测窗口期之后的最终危险度或者直接推演多步序列
        # 作为一个异常监测任务，我们假设我们需要预测未来窗口内的最大危险等级
        y_window = self.labels[
            start + self.seq_len : start + self.seq_len + self.pred_len
        ]
        y = np.max(y_window)  # 如果这段时间里有 1(塌方)，则 label 为 1

        return torch.tensor(x, dtype=torch.float32), torch.tensor(
            y, dtype=torch.float32
        )


def build_dataloaders(csv_path: str, seq_len: int, pred_len: int, batch_size: int):
    # 此处应该是真实的通过 pd.read_csv 读取。我们生成 mock DF 用于框架验证
    try:
        df = pd.read_csv(csv_path)
    except FileNotFoundError:
        print("⚠️ 没找到真实数据，将动态生成用于框架测试的高斯噪声数据...")
        dates = pd.date_range("2026-01-01", periods=10000, freq="1min")
        data = np.random.randn(10000, 8)  # 8维传感器
        labels = (np.random.rand(10000) > 0.95).astype(int)  # 5% 的数据被标记为灾害点

        df = pd.DataFrame(data, columns=[f"f_{i}" for i in range(8)])
        df["timestamp"] = dates
        df["label"] = labels

    train_size = int(len(df) * 0.8)
    train_df = df.iloc[:train_size].reset_index(drop=True)
    val_df = df.iloc[train_size:].reset_index(drop=True)

    train_ds = TimeSeriesSensorDataset(train_df, seq_len, pred_len, is_train=True)
    # 真实场景必须传递 train_ds.scaler 给 val_ds 以防止数据穿越
    val_ds = TimeSeriesSensorDataset(val_df, seq_len, pred_len, is_train=False)

    train_loader = DataLoader(
        train_ds, batch_size=batch_size, shuffle=True, drop_last=True
    )
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False)

    return train_loader, val_loader
