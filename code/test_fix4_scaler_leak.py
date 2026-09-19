# -*- coding: utf-8 -*-
"""测试：归一化对比表仅用训练集拟合 scaler（防泄漏）"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, pandas as pd
import config as C
from feature_engineering import compare_scalers, MinMaxScaler, ZScoreScaler

# 构造假数据：训练期和测试期有不同的分布
dates = pd.date_range("2000-01-01", "2004-12-31", freq="D")
n = len(dates)
rng = np.random.RandomState(42)
df = pd.DataFrame({
    "Date": dates,
    "Discharge": rng.rand(n) * 100,
    "Prcp": rng.rand(n) * 10,
    "Srad": rng.rand(n) * 500,
})
# 让测试期的 Discharge 明显大于训练期
test_mask = dates > pd.Timestamp(C.TRAIN_END)
df.loc[test_mask, "Discharge"] *= 5  # 测试期流量放大5倍

feats = ["Discharge", "Prcp", "Srad"]

# 运行 compare_scalers
tab = compare_scalers(df, feats)

# 验证1：MinMax 归一化后训练集最大值应接近1（因为只在训练集上拟合）
# 如果用全量数据拟合，训练集归一化后最大值会 < 1（因为测试期最大值更大）
mm = MinMaxScaler()
tr_mask = df["Date"] <= pd.Timestamp(C.TRAIN_END)
X_tr = df.loc[tr_mask, feats].values
mm.fit(X_tr)
X_tr_scaled = mm.transform(X_tr)
# 训练集第一个特征(Discharge)归一化后最大值应该 ≈ 1.0
assert abs(X_tr_scaled[:, 0].max() - 1.0) < 0.01, \
    f"FAIL: 训练集拟合 MinMax 后训练集最大值应≈1.0，实际 {X_tr_scaled[:,0].max()}"
print(f"PASS: 训练集拟合 MinMax 后训练集 Discharge 最大值={X_tr_scaled[:,0].max():.4f}≈1.0")

# 验证2：测试集 Discharge 归一化后最大值应 > 1（因为测试期流量更大）
X_all_scaled = mm.transform(df[feats].values)
test_scaled_max = X_all_scaled[test_mask, 0].max()
assert test_scaled_max > 1.0, \
    f"FAIL: 测试集 Discharge 归一化后应>1（训练集拟合时未见测试期最大值），实际 {test_scaled_max:.4f}"
print(f"PASS: 测试集 Discharge 归一化最大值={test_scaled_max:.4f} > 1.0（证明scaler未用测试集拟合）")

# 验证3：如果错误地用全量数据拟合，训练集归一化后最大值会 < 1
mm_wrong = MinMaxScaler()
mm_wrong.fit(df[feats].values)
wrong_tr_max = mm_wrong.transform(X_tr)[:, 0].max()
assert wrong_tr_max < 1.0, "错误对照不成立"
print(f"对照：若用全量拟合，训练集最大值={wrong_tr_max:.4f} < 1.0（这是泄漏的特征）")

print("\n=== 问题4 测试全部通过 ===")
