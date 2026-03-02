import os
import yaml
import argparse
import torch
import torch.nn as nn
import torch.optim as optim

# Import created modules
from datasets.sensor_dataset import build_dataloaders
from models.ts.multi_modal_lstm import MultiSensorLSTM


def load_config(config_path):
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def train(config_path):
    # 1. 载入核心参数
    cfg = load_config(config_path)
    print(f"🚀 开始实验: {cfg['experiment_name']}")

    device = torch.device(cfg["device"] if torch.cuda.is_available() else "cpu")
    if torch.backends.mps.is_available() and cfg["device"] in ["mps", "cuda"]:
        device = torch.device("mps")  # Mac Silicon 加速支持

    print(f"🖥 训练将在硬件上执行: {device}")

    # 2. 挂载数据 Dataloaders (这里会自动生成高斯噪声进行框架验证)
    train_loader, val_loader = build_dataloaders(
        csv_path=cfg["dataset"]["csv_path"],
        seq_len=cfg["dataset"]["seq_len"],
        pred_len=cfg["dataset"]["pred_len"],
        batch_size=cfg["dataset"]["batch_size"],
    )

    # 3. 初始化时序 LSTM 网络架构
    model = MultiSensorLSTM(
        input_dim=cfg["dataset"]["input_dim"],
        hidden_dim=cfg["model"]["hidden_dim"],
        num_layers=cfg["model"]["num_layers"],
        dropout=cfg["model"]["dropout"],
    ).to(device)

    # 4. 优化器、断点训练配置与 Loss Function
    # 对于二分类问题 (塌不塌)，我们使用 BCELoss (二元交叉熵)
    criterion = nn.BCELoss()
    optimizer = optim.Adam(
        model.parameters(),
        lr=cfg["training"]["learning_rate"],
        weight_decay=cfg["training"]["weight_decay"],
    )

    # 5. Core Epoch 循环 (反向传播与学习机制)
    best_val_loss = float("inf")
    early_stop_cnt = 0
    patience = cfg["training"]["early_stopping_patience"]
    epochs = cfg["training"]["epochs"]

    for epoch in range(1, epochs + 1):
        # ------ Training Phase ------
        model.train()
        total_train_loss = 0.0

        # tqdm 进度条可通过外挂库增加增强展示
        for batch_idx, (x, y) in enumerate(train_loader):
            x, y = x.to(device), y.to(device)

            optimizer.zero_grad()  # 梯度清零
            predictions = model(x)  # [Batch, Seq] -> [Batch, 1]
            loss = criterion(predictions, y)

            loss.backward()  # Back Propagation
            optimizer.step()  # Weight Update

            total_train_loss += loss.item()

        avg_train_loss = total_train_loss / len(train_loader)

        # ------ Validation Phase -------
        model.eval()
        total_val_loss = 0.0
        with torch.no_grad():  # 推理下停用梯度存储
            for x, y in val_loader:
                x, y = x.to(device), y.to(device)
                predictions = model(x)
                loss = criterion(predictions, y)
                total_val_loss += loss.item()

        avg_val_loss = total_val_loss / len(val_loader)

        print(
            f"Epoch [{epoch}/{epochs}] | Train Loss: {avg_train_loss:.4f} | Val Loss: {avg_val_loss:.4f}"
        )

        # ----------- 权重固化保存模块 -----------
        if avg_val_loss < best_val_loss:
            best_val_loss = avg_val_loss
            early_stop_cnt = 0
            os.makedirs(cfg["training"]["save_dir"], exist_ok=True)
            save_path = os.path.join(
                cfg["training"]["save_dir"], f"{cfg['experiment_name']}_best.pt"
            )
            torch.save(model.state_dict(), save_path)
            # print(f"✨ 发现最优模型！由于 Val Loss 更低，已写入 pt checkpoint: {save_path}")
        else:
            early_stop_cnt += 1

        if early_stop_cnt >= patience:
            print(
                f"✋ Early Stopping: 验证集在连续 {patience} 个 Epoch 未下降，训练提前结束跳出！"
            )
            break

    print("✅ 全局时序训练任务框架执行完毕！")


if __name__ == "__main__":
    # 解析命令获取运行参数
    parser = argparse.ArgumentParser(description="露井联采矿山 AI - 时序引擎训练")
    parser.add_argument(
        "--config", type=str, default="./configs/ts_base.yaml", help="算法框架核心 yaml"
    )
    args = parser.parse_args()

    train(args.config)
