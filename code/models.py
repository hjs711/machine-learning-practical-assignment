# -*- coding: utf-8 -*-
"""
第三部分：模型与超参数搜索
==========================
个体模型（3 种）：
  1. ANN     —— 人工神经网络（sklearn MLPRegressor，多层感知机）
  2. RF      —— 随机森林（sklearn RandomForestRegressor）
  3. LSTM    —— 长短期记忆网络（Keras/TensorFlow）

超参数搜索：GridSearchCV。由于是时间序列，交叉验证必须使用 TimeSeriesSplit
（前向链式切分），普通 K 折会把未来信息泄漏到训练集。

说明：Keras 模型没有 sklearn 官方封装，因此实现 LSTMModel 使其具备
fit/predict/get_params/set_params 接口，可直接接入 sklearn 的 GridSearchCV，
从而三种模型使用完全一致的超参数搜索流程。
"""

import os
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")
os.environ.setdefault("PYTHONHASHSEED", "0")

import numpy as np
from sklearn.base import BaseEstimator, RegressorMixin
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import GridSearchCV, TimeSeriesSplit
from sklearn.neural_network import MLPRegressor

import config as C

# ---------------------------------------------------------------------------
# TensorFlow 延迟导入：未安装 TF 时其余模型仍可运行
# ---------------------------------------------------------------------------
tf = None
keras = None


def _ensure_tf():
    global tf, keras
    if tf is None:
        import tensorflow as _tf
        from tensorflow import keras as _keras
        tf, keras = _tf, _keras
        tf.keras.utils.set_random_seed(C.RANDOM_STATE)
        try:
            tf.config.threading.set_intra_op_parallelism_threads(0)
            tf.config.threading.set_inter_op_parallelism_threads(0)
        except Exception:
            pass
    return tf, keras


def tf_available():
    try:
        _ensure_tf()
        return True
    except Exception as e:      # noqa: BLE001
        print(f"[warn] TensorFlow 不可用：{e}")
        return False


# ===========================================================================
# 1. LSTM —— sklearn 风格封装
# ===========================================================================
class LSTMModel(BaseEstimator, RegressorMixin):
    """Keras LSTM 回归器，接口兼容 sklearn，可直接用于 GridSearchCV。

    输入 X 的形状为 (样本数, 时间步长, 特征数)。
    输出维度 output_dim：1 表示单步预测（多步直接策略）；7 表示多输出策略。
    """

    def __init__(self, seq_len=C.SEQ_LEN, units=(64,), dropout=0.1, lr=5e-3,
                 epochs=60, batch_size=32, patience=6, output_dim=1,
                 random_state=C.RANDOM_STATE, verbose=0):
        self.seq_len = seq_len
        self.units = units
        self.dropout = dropout
        self.lr = lr
        self.epochs = epochs
        self.batch_size = batch_size
        self.patience = patience
        self.output_dim = output_dim
        self.random_state = random_state
        self.verbose = verbose

    # -- 构建网络 ----------------------------------------------------------
    def _build(self, n_features):
        _, keras = _ensure_tf()
        tf, _ = _ensure_tf()
        tf.keras.utils.set_random_seed(self.random_state)

        model = keras.Sequential()
        model.add(keras.layers.Input(shape=(self.seq_len, n_features)))
        units = tuple(self.units)
        for i, u in enumerate(units):
            return_seq = (i < len(units) - 1)
            model.add(keras.layers.LSTM(u, return_sequences=return_seq))
            model.add(keras.layers.Dropout(self.dropout))
        model.add(keras.layers.Dense(32, activation="relu"))
        model.add(keras.layers.Dense(self.output_dim))
        model.compile(optimizer=keras.optimizers.Adam(self.lr), loss="mse")
        return model

    def fit(self, X, y):
        X = np.asarray(X, dtype=np.float32)
        y = np.asarray(y, dtype=np.float32)
        if y.ndim == 1:
            y = y.reshape(-1, 1)

        # 标准 Keras fit 默认规范化层行为；这里确保 shape 一致
        self.model_ = self._build(X.shape[2])
        es = None
        _, keras = _ensure_tf()
        es = keras.callbacks.EarlyStopping(
            monitor="val_loss", patience=self.patience,
            restore_best_weights=True, min_delta=1e-5)
        self.history_ = self.model_.fit(
            X, y, epochs=self.epochs, batch_size=self.batch_size,
            validation_split=0.1,            # Keras 取末端 10%，保持时间顺序
            callbacks=[es], shuffle=False,   # 时间序列不打乱
            verbose=self.verbose)
        return self

    def predict(self, X):
        X = np.asarray(X, dtype=np.float32)
        p = self.model_.predict(X, verbose=0)
        if self.output_dim == 1:
            return p.ravel()
        return p

    @property
    def n_epochs_run(self):
        return len(self.history_.history.get("loss", []))


# ===========================================================================
# 2. 模型工厂
# ===========================================================================
def make_ann(output_dim=1, **kw):
    """人工神经网络（多层感知机）。"""
    params = dict(
        hidden_layer_sizes=(128, 64),
        activation="relu",
        solver="adam",
        alpha=1e-4,
        learning_rate_init=1e-3,
        max_iter=800,
        early_stopping=True,          # 内部按时间顺序留出末端验证集
        n_iter_no_change=25,
        validation_fraction=0.15,
        random_state=C.RANDOM_STATE,
    )
    params.update(kw)
    return MLPRegressor(**params)


def make_rf(output_dim=1, **kw):
    """随机森林（原生支持多输出，无需 MultiOutputRegressor 包装）。"""
    params = dict(
        n_estimators=300,
        max_depth=None,
        min_samples_leaf=1,
        max_features="sqrt",
        n_jobs=C.N_JOBS,
        random_state=C.RANDOM_STATE,
    )
    params.update(kw)
    return RandomForestRegressor(**params)


def make_lstm(output_dim=1, seq_len=C.SEQ_LEN, **kw):
    """LSTM 深度神经网络。"""
    params = dict(seq_len=seq_len, output_dim=output_dim)
    params.update(kw)
    return LSTMModel(**params)


# ---------------------------------------------------------------------------
# 超参数网格（为控制总计算量，取适中规模的网格）
# ---------------------------------------------------------------------------
PARAM_GRIDS = {
    "ANN": {
        "hidden_layer_sizes": [(64,), (128,), (128, 64)],
        "alpha": [1e-4, 1e-2],
        "learning_rate_init": [1e-3, 1e-2],
    },
    "RF": {
        "n_estimators": [200, 400],
        "max_depth": [None, 12, 20],
        "min_samples_leaf": [1, 3],
    },
    "LSTM": {
        "units": [(32,), (64,), (32, 32)],
        "dropout": [0.1, 0.3],
        "lr": [5e-3],
    },
}

MODEL_FACTORY = {"ANN": make_ann, "RF": make_rf, "LSTM": make_lstm}

MODEL_CN = {
    "ANN": "人工神经网络 (ANN/MLP)",
    "RF": "随机森林 (RF)",
    "LSTM": "长短期记忆网络 (LSTM)",
}


# ===========================================================================
# 3. 网格搜索
# ===========================================================================
def grid_search(model_name, X, y, seq_len=None, n_splits=None, verbose=0):
    """在时间序列交叉验证下做 GridSearchCV 超参数寻优。

    参数
    ----
    X : ndarray, (n, p) 或 (n, seq_len, p)
    y : ndarray, (n,) 或 (n, horizon)
    返回
    ----
    best_estimator, best_params, cv_table(DataFrame)
    """
    import pandas as pd
    n_splits = n_splits or C.N_CV_SPLITS
    cv = TimeSeriesSplit(n_splits=n_splits)

    grid = PARAM_GRIDS[model_name]
    output_dim = 1 if np.ndim(y) == 1 else np.asarray(y).shape[1]
    kwargs = {"output_dim": output_dim}
    if seq_len is not None:
        kwargs["seq_len"] = seq_len

    est = MODEL_FACTORY[model_name](**kwargs)
    gs = GridSearchCV(
        est, grid, cv=cv,
        scoring="neg_root_mean_squared_error",
        n_jobs=1,          # Keras 模型不可多进程；统一单进程便于复现
        verbose=verbose, refit=True,
    )
    gs.fit(X, y)

    cv_table = pd.DataFrame(gs.cv_results_)[
        ["params", "mean_test_score", "std_test_score", "rank_test_score"]
    ].sort_values("rank_test_score").reset_index(drop=True)
    cv_table["mean_test_RMSE"] = -cv_table["mean_test_score"]
    cv_table = cv_table.drop(columns=["mean_test_score"])
    return gs.best_estimator_, gs.best_params_, cv_table
