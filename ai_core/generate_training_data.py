"""
穹盾智矿 - 合成传感器训练数据生成器
===========================================
生成真实感的矿山多维传感器时序数据，用于 LSTM 模型训练

数据特征（4维）：
  1. crack_width_mm    裂缝宽度(mm)     正常: 0.5~3.0, 危险: 8~20
  2. seismic_energy_j   微震能量(J)      正常: 5~30, 危险: 100~300
  3. angle_x_deg        倾角(°)          正常: 0.01~0.3, 危险: 1.5~4.0
  4. settlement_mm      沉降量(mm)       正常: 0.2~2.0, 危险: 8~25

标签： 0=安全, 1=危险（未来窗口内存在塌方风险）

模拟策略：
  - 90% 的时间段为正常平稳波动
  - 10% 的时间段出现"渐进式风险累积"（而不是突变，更真实）
  - 风险前兆：裂缝缓慢增大 → 微震频率增加 → 倾角变化 → 最终沉降突破阈值
"""

import os
import numpy as np
import pandas as pd

np.random.seed(42)

TOTAL_MINUTES = 20000  # 约14天的分钟级数据
OUTPUT_PATH = "./data/synthetic_sensor_data.csv"


def generate_normal_segment(length):
    """生成一段正常运行期的传感器读数"""
    crack = np.random.normal(1.5, 0.5, length).clip(0.1, 4.0)
    seismic = np.random.normal(15, 8, length).clip(1, 50)
    angle = np.random.normal(0.1, 0.05, length).clip(0.01, 0.5)
    settlement = np.random.normal(1.0, 0.4, length).clip(0.1, 3.0)
    labels = np.zeros(length)
    return crack, seismic, angle, settlement, labels


def generate_risk_buildup(length):
    """
    生成一段渐进式风险累积序列
    模拟真实地质变化：裂缝缓慢增大 → 微震增强 → 倾角偏移 → 沉降加速
    """
    t = np.linspace(0, 1, length)

    # 指数式渐变 + 噪声
    crack = (
        1.5
        + 15.0 * (np.exp(2 * t) - 1) / (np.exp(2) - 1)
        + np.random.normal(0, 0.5, length)
    )
    seismic = 15 + 250.0 * t**2 + np.random.normal(0, 10, length)
    angle = 0.1 + 3.0 * t**1.5 + np.random.normal(0, 0.1, length)
    settlement = 1.0 + 20.0 * t**2.5 + np.random.normal(0, 0.5, length)

    crack = crack.clip(0.1, 25)
    seismic = seismic.clip(1, 400)
    angle = angle.clip(0.01, 5)
    settlement = settlement.clip(0.1, 30)

    # 前40%的序列标为安全（前兆期），后60%标为危险
    labels = np.zeros(length)
    labels[int(length * 0.4) :] = 1.0

    return crack, seismic, angle, settlement, labels


def main():
    all_crack, all_seismic, all_angle, all_settle, all_labels = [], [], [], [], []

    remaining = TOTAL_MINUTES
    segment_id = 0

    while remaining > 0:
        # 决定这个片段是正常还是风险
        is_risk = np.random.rand() < 0.10  # 10%概率出现风险

        if is_risk:
            seg_len = min(np.random.randint(120, 360), remaining)  # 风险持续2~6小时
            c, s, a, st, lab = generate_risk_buildup(seg_len)
            segment_id += 1
            print(
                f"  ⚠️  风险段 #{segment_id}: {seg_len} 分钟 (t={TOTAL_MINUTES - remaining}~{TOTAL_MINUTES - remaining + seg_len})"
            )
        else:
            seg_len = min(np.random.randint(200, 800), remaining)  # 正常3~13小时
            c, s, a, st, lab = generate_normal_segment(seg_len)

        all_crack.append(c)
        all_seismic.append(s)
        all_angle.append(a)
        all_settle.append(st)
        all_labels.append(lab)
        remaining -= seg_len

    # 拼接
    crack = np.concatenate(all_crack)
    seismic = np.concatenate(all_seismic)
    angle = np.concatenate(all_angle)
    settlement = np.concatenate(all_settle)
    labels = np.concatenate(all_labels)

    timestamps = pd.date_range("2026-01-01", periods=len(crack), freq="1min")

    df = pd.DataFrame(
        {
            "timestamp": timestamps,
            "crack_width_mm": crack.round(3),
            "seismic_energy_j": seismic.round(2),
            "angle_x_deg": angle.round(4),
            "settlement_mm": settlement.round(3),
            "label": labels.astype(int),
        }
    )

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    df.to_csv(OUTPUT_PATH, index=False)

    total = len(df)
    risk_count = (df["label"] == 1).sum()
    print(f"\n✅ 合成数据集生成完毕!")
    print(f"   总样本: {total} 条 ({total/60:.1f} 小时)")
    print(f"   危险样本: {risk_count} ({risk_count/total*100:.1f}%)")
    print(f"   安全样本: {total - risk_count} ({(total-risk_count)/total*100:.1f}%)")
    print(f"   保存至: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
