import pickle
from typing import Union

import pandas as pd
from hydra.utils import instantiate
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.linear_model import LinearRegression


SklearnRegressionModel = Union[GradientBoostingRegressor, LinearRegression]


def train_model(
    model_params, train_features: pd.DataFrame, target: pd.Series
) -> SklearnRegressionModel:
    model = instantiate(model_params).fit(train_features, target)
    return model


def serialize_model(model: SklearnRegressionModel, output: str) -> str:
    with open(output, "wb") as f:
        pickle.dump(model, f)
    return output
