# -*- coding: utf-8 -*-
import os
from typing import List, Optional, Tuple

import pandas as pd
from sklearn.model_selection import train_test_split


DATE_COLUMNS = [
    "order_purchase_timestamp",
    "order_aproved_at",
    "order_estimated_delivery_date",
    "order_delivered_customer_date",
]


def read_data(dataset_path: str) -> pd.DataFrame:
    """Read Olist orders CSV, parse dates, merge category translation."""
    data = pd.read_csv(dataset_path)
    for col in DATE_COLUMNS:
        if col in data.columns:
            data[col] = pd.to_datetime(data[col], errors="coerce")

    translation_path = os.path.join(
        os.path.dirname(os.path.abspath(dataset_path)),
        "product_category_name_translation.csv",
    )
    if os.path.exists(translation_path) and "product_category_name" in data.columns:
        translation = pd.read_csv(translation_path)
        data = data.merge(translation, on="product_category_name", how="left").drop(
            columns=["product_category_name"]
        )
    return data


def drop_unused_columns(
    data: pd.DataFrame, features_to_drop: Optional[List[str]]
) -> pd.DataFrame:
    """Drop identifier / leakage columns."""
    if not features_to_drop:
        return data
    cols = [c for c in features_to_drop if c in data.columns]
    return data.drop(columns=cols)


def split_train_test_data(
    data: pd.DataFrame,
    target_col: str,
    test_size: float,
    random_state: int,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Stratified train/test split by target column."""
    train_df, test_df = train_test_split(
        data,
        test_size=test_size,
        random_state=random_state,
        stratify=data[target_col],
    )
    return train_df.reset_index(drop=True), test_df.reset_index(drop=True)
