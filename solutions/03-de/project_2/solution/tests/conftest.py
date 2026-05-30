import tempfile
from typing import List

import pandas as pd
import pytest

from satisfaction.data.make_dataset import read_data
from satisfaction.entities import (
    LinRegConfig,
    GBRConfig,
    SplittingConfig,
    FeatureConfig,
    DatasetConfig,
)
from tests.data_generator import generate_dataset, generate_engineered_dataset


@pytest.fixture(scope="session")
def dataset_path() -> str:
    data = generate_dataset()
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as temp:
        data.to_csv(temp, index=False)
    return temp.name


@pytest.fixture(scope="session")
def dataset(dataset_path) -> pd.DataFrame:
    return read_data(dataset_path)


@pytest.fixture(scope="session")
def engineered_dataset() -> pd.DataFrame:
    """Dataset with engineered features already added (does not depend on AttributesAdder)."""
    return generate_engineered_dataset()


@pytest.fixture(scope="session")
def target_col() -> str:
    return "review_score"


@pytest.fixture(scope="session")
def categorical_features() -> List[str]:
    return [
        "order_status",
        "customer_state",
        "product_category_name_english",
    ]


@pytest.fixture(scope="session")
def numerical_features() -> List[str]:
    return [
        "order_products_value",
        "order_freight_value",
        "order_items_qty",
        "order_sellers_qty",
        "product_name_lenght",
        "product_description_lenght",
        "product_photos_qty",
        "wd_estimated_delivery_time",
        "wd_actual_delivery_time",
        "wd_delivery_time_delta",
        "is_late",
        "average_product_value",
        "total_order_value",
        "order_freight_ratio",
        "purchase_dayofweek",
    ]


@pytest.fixture(scope="session")
def features_to_drop() -> List[str]:
    return [
        "order_id",
        "customer_id",
        "product_id",
        "review_id",
        "customer_city",
        "customer_zip_code_prefix",
        "review_comment_title",
        "review_comment_message",
        "review_creation_date",
        "review_answer_timestamp",
    ]


@pytest.fixture(scope="class")
def lin_reg_model() -> LinRegConfig:
    return LinRegConfig(
        _target_="sklearn.linear_model.LinearRegression",
        fit_intercept=True,
    )


@pytest.fixture(scope="class")
def gbr_model() -> GBRConfig:
    return GBRConfig(
        _target_="sklearn.ensemble.GradientBoostingRegressor",
        n_estimators=20,
        max_depth=3,
        learning_rate=0.1,
        random_state=42,
    )


@pytest.fixture(scope="session")
def split_config_v1() -> SplittingConfig:
    return SplittingConfig(test_size=0.25, random_state=42)


@pytest.fixture(scope="session")
def feature_param_v1(
    categorical_features,
    numerical_features,
    target_col,
    features_to_drop,
) -> FeatureConfig:
    return FeatureConfig(
        categorical_features=categorical_features,
        numerical_features=numerical_features,
        target_col=target_col,
        categorical_encoder="onehot",
        features_to_drop=features_to_drop,
    )


@pytest.fixture(scope="session")
def dataset_config_v1(dataset_path) -> DatasetConfig:
    return DatasetConfig(input_data_path=dataset_path)
