# -*- coding: utf-8 -*-
"""
测试：Stacking 多输出 OOF 分布不匹配修复
验证：多输出策略下，OOF 模型使用 output_dim=HORIZON(7)，而非 output_dim=1
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
import config as C
import experiment as E

# --- 构造一个最小 DataBundle 用于测试 ---
def make_fake_bundle(n=200, n_feat=5):
    """构造一个假的 DataBundle，仅用于验证 OOF 模型构造逻辑。"""
    class FakeDS:
        pass
    ds = FakeDS()
    ds.START = 10
    ds.train_end = 150
    ds.N = n
    ds.dates = np.arange(n)
    # 假数据
    rng = np.random.RandomState(42)
    ds.Xraw = rng.randn(n, n_feat)
    ds.y = np.cumsum(rng.randn(n)) + 100
    ds.ys = ds.y
    ds.Xs = ds.Xraw
    # X_of: ANN/RF 用 2D，LSTM 用 3D
    ds._origins_call = []
    def X_of(origins, model_name):
        ds._origins_call.append((model_name, len(origins)))
        return ds.Xs[origins]
    ds.X_of = X_of
    ds.y_direct = lambda origins, h: ds.ys[origins + h]
    ds.y_multi = lambda origins: np.column_stack([ds.ys[origins + k] for k in range(1, C.HORIZON + 1)])
    ds.inv_y = lambda v: v
    ds.true_at = lambda origins, h: ds.y[origins + h]
    return ds

# --- 用 mock 捕获模型工厂的调用参数 ---
captured = []
orig_factory = E.M.MODEL_FACTORY

def mock_factory(model_name, **kw):
    captured.append({"model_name": model_name, "output_dim": kw.get("output_dim")})
    # 返回一个能 fit/predict 的假模型
    od = kw.get("output_dim", 1)
    class FakeEst:
        def fit(self, X, y):
            return self
        def predict(self, X):
            n = X.shape[0]
            return np.random.randn(n, od) if od > 1 else np.random.randn(n)
    return FakeEst()

E.M.MODEL_FACTORY = {"ANN": lambda **kw: mock_factory("ANN", **kw),
                     "RF":  lambda **kw: mock_factory("RF", **kw),
                     "LSTM":lambda **kw: mock_factory("LSTM", **kw)}

# 构造假的 base_preds 和 base_est_params
n_test = 50
base_preds = {
    "ANN": {"multi": {h: {"pred_scaled": np.random.randn(n_test)} for h in range(1, 8)}},
    "RF":  {"multi": {h: {"pred_scaled": np.random.randn(n_test)} for h in range(1, 8)}},
}
base_est_params = {
    "ANN": {"multi": {h: {} for h in range(1, 8)}},
    "RF":  {"multi": {h: {} for h in range(1, 8)}},
}

ds = make_fake_bundle()

# === 测试多输出策略 ===
captured.clear()
out, coef = E.ensemble_stacking(ds, "multi", base_preds, base_est_params,
                                 ["ANN", "RF"])

# 验证：多输出策略下所有 OOF 模型都应该是 output_dim=7
multi_dims = [c["output_dim"] for c in captured]
print(f"[多输出] OOF 模型 output_dim 调用记录: {multi_dims}")
assert all(d == C.HORIZON for d in multi_dims), \
    f"FAIL: 多输出策略 OOF 应使用 output_dim={C.HORIZON}，实际得到 {set(multi_dims)}"
print("PASS: 多输出策略 OOF 模型全部使用 output_dim=7")

# === 测试直接策略（应保持 output_dim=1）===
base_preds_d = {
    "ANN": {"direct": {h: {"pred_scaled": np.random.randn(n_test)} for h in range(1, 8)}},
    "RF":  {"direct": {h: {"pred_scaled": np.random.randn(n_test)} for h in range(1, 8)}},
}
base_est_params_d = {
    "ANN": {"direct": {h: {} for h in range(1, 8)}},
    "RF":  {"direct": {h: {} for h in range(1, 8)}},
}
captured.clear()
out_d, coef_d = E.ensemble_stacking(ds, "direct", base_preds_d, base_est_params_d,
                                    ["ANN", "RF"])
direct_dims = [c["output_dim"] for c in captured]
print(f"[直接] OOF 模型 output_dim 调用记录: {direct_dims}")
assert all(d == 1 for d in direct_dims), \
    f"FAIL: 直接策略 OOF 应使用 output_dim=1，实际得到 {set(direct_dims)}"
print("PASS: 直接策略 OOF 模型全部使用 output_dim=1")

E.M.MODEL_FACTORY = orig_factory
print("\n=== 问题2 测试全部通过 ===")
