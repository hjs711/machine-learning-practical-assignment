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
# 注意：PYTHONHASHSEED 必须在 Python 解释器启动前设置才有效，
# 在脚本内设置无效，因此不在此处设置；如需复现请用 PYTHONHASHSEED=0 python run_all.py

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
    """人工神经网络（多层感知机）。

    注意：sklearn MLPRegressor 的 early_stopping=True 内部调用
    train_test_split(shuffle=True) 随机划分验证集，对时间序列构成数据泄漏。
    因此这里关闭内置 early_stopping，依赖：
      (1) L2 正则化 alpha（由 GridSearchCV 选优）防止过拟合；
      (2) 充分的 max_iter 保证收敛；
      (3) 外层 TimeSeriesSplit 选出最优泛化模型。
    """
    params = dict(
        hidden_layer_sizes=(128, 64),
        activation="relu",
        solver="adam",
        alpha=1e-4,
        learning_rate_init=1e-3,
        max_iter=2000,
        early_stopping=False,         # 禁用随机划分验证集，防时间序列泄漏
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
        "hidden_layer_sizes": [(64,), (128,), (128, 64), (256, 128)],
        "alpha": [1e-5, 1e-4, 1e-2],
        "learning_rate_init": [5e-4, 1e-3, 1e-2],
    },
    "RF": {
        "n_estimators": [200, 300, 400, 500],
        "max_depth": [None, 10, 12, 15, 20, 25],
        "min_samples_leaf": [1, 3, 5],
    },
    "LSTM": {
        "units": [(32,), (64,), (32, 32), (64, 32)],
        "dropout": [0.1, 0.2, 0.3],
        "lr": [5e-3, 1e-3],
        "epochs": [60, 80],
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


# ===========================================================================
# 4. 模型持久化与热启动（warm start）
#    训练好的最优模型保存到磁盘，下次运行时在已有权重基础上继续训练，
#    而非每次随机初始化从零开始。
# ===========================================================================
def _model_path(model_name, strategy, h):
    """生成模型保存路径。"""
    fname = f"{model_name}_{strategy}_h{h}.joblib"
    return os.path.join(C.MODEL_DIR, fname)


def save_model(model, model_name, strategy, h):
    """保存训练好的模型到磁盘。"""
    import joblib
    path = _model_path(model_name, strategy, h)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if model_name == "LSTM":
        # Keras 模型权重单独保存
        keras_path = path.replace(".joblib", ".keras.weights.h5")
        model.model_.save_weights(keras_path)
        joblib.dump({"_keras_weights_path": keras_path}, path)
    else:
        joblib.dump(model, path)
    return path


def load_model(model_name, strategy, h):
    """从磁盘加载已保存的模型；不存在返回 None。"""
    import joblib
    path = _model_path(model_name, strategy, h)
    if not os.path.exists(path):
        return None
    try:
        return joblib.load(path)
    except Exception:
        return None


def warm_start_train(model_name, X, y, best_params, strategy, h,
                     seq_len=None, extra_iter=500):
    """在已有最优模型基础上继续训练（热启动）。

    - ANN：设置 warm_start=True，在已有权重上继续梯度下降
    - RF：设置 warm_start=True，在已有树基础上增加新树
    - LSTM：加载已保存的 Keras 权重，继续训练更多 epochs

    返回训练后的模型；没有已保存模型时返回 None。
    """
    saved = load_model(model_name, strategy, h)
    if saved is None:
        return None

    output_dim = 1 if np.ndim(y) == 1 else np.asarray(y).shape[1]
    kw = dict(best_params)

    if model_name == "ANN":
        est = make_ann(output_dim=output_dim, **kw)
        est.warm_start = True       # sklearn 关键参数：继续训练而非重新初始化
        est.max_iter = extra_iter
        est.fit(X, y)
        print(f"    [热启动] ANN h={h}  从已保存模型继续训练 {extra_iter} 轮")
        return est

    elif model_name == "RF":
        est = make_rf(output_dim=output_dim, **kw)
        est.warm_start = True       # 在已有树基础上增加新树
        est.n_estimators = extra_iter
        est.fit(X, y)
        print(f"    [热启动] RF  h={h}  从已保存模型增加 {extra_iter} 棵树")
        return est

    elif model_name == "LSTM":
        keras_path = _model_path(model_name, strategy, h).replace(
            ".joblib", ".keras.weights.h5")
        if not os.path.exists(keras_path):
            return None
        seq_len_val = seq_len or C.SEQ_LEN
        est = make_lstm(output_dim=output_dim, seq_len=seq_len_val, **kw)
        X_sample = np.asarray(X[:1], dtype=np.float32)
        est.model_ = est._build(X_sample.shape[2])
        est.model_.load_weights(keras_path)
        y_arr = np.asarray(y, dtype=np.float32)
        if y_arr.ndim == 1:
            y_arr = y_arr.reshape(-1, 1)
        _, keras = _ensure_tf()
        es = keras.callbacks.EarlyStopping(
            monitor="val_loss", patience=est.patience,
            restore_best_weights=True, min_delta=1e-5)
        est.model_.fit(
            np.asarray(X, dtype=np.float32), y_arr,
            epochs=extra_iter, batch_size=est.batch_size,
            validation_split=0.1, callbacks=[es], shuffle=False, verbose=0)
        print(f"    [热启动] LSTM h={h}  从已保存权重继续训练 {extra_iter} epochs")
        return est

    return None
