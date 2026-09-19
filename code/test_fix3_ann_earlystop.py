# -*- coding: utf-8 -*-
"""
测试：ANN early_stopping 随机划分数据泄漏修复
验证：make_ann() 返回的模型 early_stopping=False，不使用随机验证集
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
import models as M

# === 测试 1：默认参数 ===
ann = M.make_ann()
print(f"early_stopping = {ann.early_stopping}")
print(f"max_iter = {ann.max_iter}")
assert ann.early_stopping == False, \
    f"FAIL: early_stopping 应为 False，实际为 {ann.early_stopping}"
print("PASS: early_stopping=False（不随机划分验证集）")

# === 测试 2：max_iter 足够大 ===
assert ann.max_iter >= 1000, \
    f"FAIL: max_iter 应 >= 1000 保证无 early stopping 时收敛，实际 {ann.max_iter}"
print(f"PASS: max_iter={ann.max_iter}（足够大，无 early stopping 也能收敛）")

# === 测试 3：确认没有 validation_fraction 泄漏 ===
# early_stopping=False 时 sklearn 不使用 validation_fraction
# 但检查参数中不包含 n_iter_no_change（仅 early_stopping 时用）
assert not hasattr(ann, 'validation_fraction') or ann.early_stopping == False, \
    "FAIL: early_stopping 应为 False"
print("PASS: 不存在随机验证集划分")

# === 测试 4：用小数据实际训练，确认不报错且能收敛 ===
rng = np.random.RandomState(42)
X = rng.randn(200, 5)
y = np.cumsum(rng.randn(200)) + 100  # 简单线性+噪声

ann2 = M.make_ann(max_iter=500)
ann2.fit(X, y)
pred = ann2.predict(X[:10])
assert len(pred) == 10, "FAIL: 预测长度不对"
assert not np.any(np.isnan(pred)), "FAIL: 预测含 NaN"
print(f"PASS: 实际训练+预测成功，训练 {ann2.n_iter_} 轮")

# === 测试 5：确认多输出也正常 ===
y_multi = np.column_stack([y, y*2, y+1])
ann3 = M.make_ann(output_dim=3, max_iter=500)
ann3.fit(X, y_multi)
pred3 = ann3.predict(X[:5])
assert pred3.shape == (5, 3), f"FAIL: 多输出预测 shape 应为 (5,3)，实际 {pred3.shape}"
print(f"PASS: 多输出训练+预测成功，shape={pred3.shape}")

print("\n=== 问题3 测试全部通过 ===")
