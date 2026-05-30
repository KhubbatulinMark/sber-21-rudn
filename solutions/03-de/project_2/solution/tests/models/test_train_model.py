from typing import List, Tuple

import pandas as pd
import pytest

from sklearn.ensemble import GradientBoostingRegressor
from sklearn.linear_model import LinearRegression

from satisfaction.entities import FeatureConfig, GBRConfig, LinRegConfig
from satisfaction.features import build_transformer, extract_target, make_features
from satisfaction.models.fit import train_model


@pytest.fixture
def features_and_target(
    engineered_dataset: pd.DataFrame,
    categorical_features: List[str],
    numerical_features: List[str],
    target_col: str,
) -> Tuple[pd.DataFrame, pd.Series]:
    params = FeatureConfig(
        categorical_features=categorical_features,
        numerical_features=numerical_features,
        features_to_drop=[],
        target_col=target_col,
        categorical_encoder="onehot",
    )
    transformer = build_transformer(
        categorical_features, numerical_features, params.categorical_encoder
    )
    transformer.fit(engineered_dataset)
    features = make_features(transformer, engineered_dataset)
    target = extract_target(engineered_dataset, params.target_col)
    return features, target


@pytest.mark.parametrize(
    "model_config, model_class",
    [
        (LinRegConfig(), LinearRegression),
        (
            GBRConfig(n_estimators=20, max_depth=3, learning_rate=0.1, random_state=42),
            GradientBoostingRegressor,
        ),
    ],
    ids=["linreg", "gbr"],
)
def test_train_model(
    features_and_target: Tuple[pd.DataFrame, pd.Series], model_config, model_class
):
    features, target = features_and_target
    model = train_model(model_config, features, target)
    assert isinstance(model, model_class)
