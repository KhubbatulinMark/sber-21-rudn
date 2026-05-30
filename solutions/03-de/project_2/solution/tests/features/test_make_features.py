from typing import List

import pandas as pd
import pytest
from numpy.testing import assert_allclose

from satisfaction.entities.feature import FeatureConfig
from satisfaction.features import build_transformer, extract_target, make_features
from satisfaction.features.build_features import OutlierRemover


@pytest.fixture
def feature_params(
    categorical_features: List[str],
    features_to_drop: List[str],
    numerical_features: List[str],
    target_col: str,
) -> FeatureConfig:
    return FeatureConfig(
        categorical_features=categorical_features,
        numerical_features=numerical_features,
        features_to_drop=features_to_drop,
        target_col=target_col,
        categorical_encoder="onehot",
    )


def test_make_features(
    feature_params: FeatureConfig, engineered_dataset: pd.DataFrame
):
    """After transformation there are no missing values and the row count is preserved."""
    transformer = build_transformer(
        feature_params.categorical_features,
        feature_params.numerical_features,
        feature_params.categorical_encoder,
    )
    transformer.fit(engineered_dataset)
    features = make_features(transformer, engineered_dataset)
    assert not pd.isnull(features).any().any()
    assert len(features) == len(engineered_dataset)
    # feature dimensionality must be at least the number of numerical features + 1 one-hot column
    assert features.shape[1] >= len(feature_params.numerical_features) + 1


def test_outlier_transformer(
    engineered_dataset: pd.DataFrame, numerical_features: List[str]
):
    outlier_remover = OutlierRemover(1.5)
    result = outlier_remover.fit_transform(engineered_dataset[numerical_features])
    q1 = engineered_dataset[numerical_features].quantile(0.25)
    q3 = engineered_dataset[numerical_features].quantile(0.75)
    iqr = q3 - q1
    lower_bound = q1 - (1.5 * iqr)
    upper_bound = q3 + (1.5 * iqr)
    result = result.fillna(result.mean())
    assert sum(((result < lower_bound) | (result > upper_bound)).sum()) == 0


def test_extract_features(
    feature_params: FeatureConfig, engineered_dataset: pd.DataFrame
):
    target = extract_target(engineered_dataset, feature_params.target_col)
    assert_allclose(engineered_dataset[feature_params.target_col].values, target)
