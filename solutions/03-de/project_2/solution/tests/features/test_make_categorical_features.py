from typing import List

import numpy as np
import pandas as pd
import pytest

from satisfaction.features.build_features import (
    TargetEncoder,
    build_categorical_pipeline,
    process_categorical_features,
)


@pytest.fixture()
def categorical_feature() -> str:
    return "categorical_feature"


@pytest.fixture()
def categorical_values() -> List[str]:
    return ["cat", "dog", "parrot"]


@pytest.fixture()
def categorical_values_with_nan(categorical_values: List[str]) -> List[str]:
    return categorical_values + [np.nan]


@pytest.fixture
def fake_categorical_data(
    categorical_feature: str, categorical_values_with_nan: List[str]
) -> pd.DataFrame:
    return pd.DataFrame({categorical_feature: categorical_values_with_nan})


def test_process_categorical_features(
    fake_categorical_data: pd.DataFrame,
    categorical_feature: str,
    categorical_values: List[str],
):
    """SimpleImputer + OneHot: missing values are filled with the mode, unique = 3 values."""
    transformed: pd.DataFrame = process_categorical_features(fake_categorical_data)
    assert 3 == transformed.shape[1]
    # after imputer the missing value is filled with the most frequent category => sum = 4
    assert 4 == transformed.sum().sum()


def test_target_encoder_smoothing():
    """Target encoder with smoothing: a rare category is pulled toward the global mean."""
    x = pd.DataFrame({"c": ["a"] * 100 + ["b"] * 1})
    y = pd.Series([5.0] * 100 + [1.0])
    encoder = TargetEncoder(smoothing=10.0)
    encoder.fit(x, y)
    encoded = encoder.transform(x)
    global_mean = y.mean()
    a_encoded = encoded.iloc[0, 0]
    b_encoded = encoded.iloc[-1, 0]
    # Frequent category stays close to its own mean (5.0)
    assert abs(a_encoded - 5.0) < abs(a_encoded - global_mean)
    # Rare category is pulled toward the global mean
    assert abs(b_encoded - global_mean) < abs(b_encoded - 1.0)


def test_build_categorical_pipeline_switch():
    """Switching the encoding strategy via the encoder parameter."""
    onehot = build_categorical_pipeline("onehot")
    target = build_categorical_pipeline("target")
    assert onehot is not None
    assert target is not None
    # Different strategies – different final steps
    assert type(onehot.steps[-1][1]).__name__ != type(target.steps[-1][1]).__name__
