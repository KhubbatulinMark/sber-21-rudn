"""Self-contained baseline training, mirroring the satisfaction pipeline of project 2.

For full integration with the project 2 hydra pipeline, copy `satisfaction/` into
`include/satisfaction/` and import `train_pipeline` from there. This module keeps the
solution stand-alone so it can be evaluated without project 2 artefacts.
"""

import json
import pickle
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, roc_auc_score
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from include.drift.sql import CATEGORICAL_FEATURES, NUMERICAL_FEATURES, TARGET

MODELS = {
    "lr": lambda: LinearRegression(),
    "gbr": lambda: GradientBoostingRegressor(
        n_estimators=200, max_depth=3, learning_rate=0.05, random_state=42
    ),
}


def _build_transformer() -> ColumnTransformer:
    numerical = Pipeline([
        ("impute", SimpleImputer(strategy="median")),
        ("scale", StandardScaler(with_mean=False)),
    ])
    categorical = Pipeline([
        ("impute", SimpleImputer(strategy="most_frequent")),
        ("encode", OneHotEncoder(handle_unknown="ignore", min_frequency=20)),
    ])
    return ColumnTransformer([
        ("num", numerical, NUMERICAL_FEATURES),
        ("cat", categorical, CATEGORICAL_FEATURES),
    ])


def train_model(data_path: Path, model_name: str, output_dir: Path) -> dict:
    df = pd.read_parquet(data_path).dropna(subset=[TARGET])
    X = df[NUMERICAL_FEATURES + CATEGORICAL_FEATURES]
    y = df[TARGET].astype(float)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y.round().astype(int)
    )
    transformer = _build_transformer()
    transformer.fit(X_train, y_train)
    X_train_t = transformer.transform(X_train)
    X_test_t = transformer.transform(X_test)

    model = MODELS[model_name]()
    try:
        cv_scores = cross_val_score(
            model, X_train_t, (y_train >= 4).astype(int), cv=3, scoring="roc_auc"
        )
        cv_mean, cv_std = float(np.nanmean(cv_scores)), float(np.nanstd(cv_scores))
    except Exception:
        cv_mean, cv_std = 0.0, 0.0
    model.fit(X_train_t, y_train)

    preds = model.predict(X_test_t)
    rmse = float(np.sqrt(mean_squared_error(y_test, preds)))
    roc = float(roc_auc_score((y_test >= 4).astype(int), preds))

    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "model.pkl").write_bytes(pickle.dumps(model))
    (output_dir / "transformer.pkl").write_bytes(pickle.dumps(transformer))
    metrics = {
        "model_name": model_name,
        "rmse": rmse,
        "roc_auc": roc,
        "cv_roc_auc_mean": cv_mean if not np.isnan(cv_mean) else 0.0,
        "cv_roc_auc_std": cv_std if not np.isnan(cv_std) else 0.0,
    }
    (output_dir / "metrics.json").write_text(json.dumps(metrics, indent=2))
    return metrics
