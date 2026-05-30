from typing import Dict, Union

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, roc_auc_score

SklearnRegressionModel = Union[GradientBoostingRegressor, LinearRegression]


def predict_model(
    model: SklearnRegressionModel, features: pd.DataFrame
) -> np.ndarray:
    return model.predict(features)


def evaluate_model(
    predicts: np.ndarray, target: pd.Series, positive_threshold: int = 4
) -> Dict[str, float]:
    target = np.asarray(target).ravel()
    predicts = np.asarray(predicts).ravel()
    metrics: Dict[str, float] = {
        "rmse": float(np.sqrt(mean_squared_error(target, predicts))),
    }
    binary = (target >= positive_threshold).astype(int)
    if len(np.unique(binary)) > 1:
        metrics["roc_auc"] = float(roc_auc_score(binary, predicts))
    else:
        metrics["roc_auc"] = float("nan")
    return metrics
