import numpy as np
import pandas as pd

from satisfaction.data.make_dataset import (
    drop_unused_columns,
    read_data,
    split_train_test_data,
)


def test_load_dataset(dataset_path: str, target_col: str):
    data = read_data(dataset_path)
    assert len(data) == 100
    assert target_col in data.keys()


def test_drop_unused_columns(dataset: pd.DataFrame):
    to_drop = ["order_id", "customer_id"]
    result = drop_unused_columns(dataset, to_drop)
    for col in to_drop:
        assert col not in result.columns
    assert "order_status" in result.columns


def test_split_dataset(dataset: pd.DataFrame, target_col: str):
    train_df, test_df = split_train_test_data(
        dataset, target_col=target_col, test_size=0.25, random_state=42
    )
    assert len(train_df) + len(test_df) == len(dataset)
    assert abs(len(test_df) - 25) <= 2

    full_dist = dataset[target_col].value_counts(normalize=True).sort_index()
    train_dist = train_df[target_col].value_counts(normalize=True).sort_index()
    # class distributions in train and in the original dataset should be close
    np.testing.assert_allclose(
        train_dist.values, full_dist.values, atol=0.05
    )
