import torch
import torch.nn as nn


class MultiSensorLSTM(nn.Module):
    """
    针对露井联采多维传感器的 LSTM 时空预测模型
    将裂缝(Vision提取特征)、位移(IoT)、水文应力(IoT)特征在时间维度融合预测
    """

    def __init__(
        self, input_dim: int, hidden_dim: int, num_layers: int, dropout: float = 0.2
    ):
        super(MultiSensorLSTM, self).__init__()

        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers

        # 核心：长短期记忆网络，用于提取时间依赖
        self.lstm = nn.LSTM(
            input_size=input_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,  # 输入格式 [batch, seq_len, features]
            dropout=dropout if num_layers > 1 else 0,
        )

        # 将 LSTM 的最后一个 Cell 的隐状态映射到分类特征 (预测危险发生概率)
        self.fc1 = nn.Linear(hidden_dim, 64)
        self.relu = nn.ReLU()
        self.dropout = nn.Dropout(dropout)

        # 最后一层：单点输出（Sigmoid用于二分类，或者输出多维度的预测）
        self.fc2 = nn.Linear(64, 1)
        self.sigmoid = nn.Sigmoid()

    def forward(self, x):
        """
        x: shape (batch_size, seq_len, input_dim)
        """
        # 初始化隐藏状态和细胞状态 (默认可以由 PyTorch 自动初始化，也可显式传入)
        # h0, c0 defaults to zero if not provided
        out, (hn, cn) = self.lstm(x)

        # 我们只关心序列预测的"最后一个时间步"的状态用来推理未来风险
        # out[:, -1, :] shape: (batch_size, hidden_dim)
        last_hidden_state = out[:, -1, :]

        # 全连接层映射
        x_dense = self.dropout(self.relu(self.fc1(last_hidden_state)))
        prediction = self.sigmoid(self.fc2(x_dense)).squeeze(-1)  # Shape: (batch_size)

        return prediction
