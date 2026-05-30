"""Synthetic Olist-like datasets for tests.

Two factories:
- `generate_dataset` – raw dataset as if loaded from CSV (without engineered features);
- `generate_engineered_dataset` – dataset with engineered features already
  added (so that tests for `build_transformer` do not depend on the student's
  implementation of `AttributesAdder`).
"""
import numpy as np
import pandas as pd


STATES = ["SP", "RJ", "MG", "PR", "RS", "SC", "BA", "GO"]
STATUSES = ["delivered", "shipped", "canceled", "processing"]
CATEGORIES = [
    "beleza_saude",
    "informatica_acessorios",
    "automotivo",
    "cama_mesa_banho",
    "esporte_lazer",
]


def __rand_timestamps(size: int, start: str, end: str) -> pd.Series:
    start_ts = pd.Timestamp(start).value
    end_ts = pd.Timestamp(end).value
    values = np.random.randint(start_ts, end_ts, size=size)
    return pd.to_datetime(values)


def generate_dataset(dataset_size: int = 100, seed: int = 42) -> pd.DataFrame:
    np.random.seed(seed)
    df = pd.DataFrame()
    df["order_id"] = [f"order_{i}" for i in range(dataset_size)]
    df["order_status"] = np.random.choice(STATUSES, size=dataset_size)
    df["order_products_value"] = np.round(
        np.random.uniform(10, 500, size=dataset_size), 2
    )
    df["order_freight_value"] = np.round(
        np.random.uniform(5, 50, size=dataset_size), 2
    )
    df["order_items_qty"] = np.random.randint(1, 5, size=dataset_size)
    df["order_sellers_qty"] = np.random.randint(1, 3, size=dataset_size)

    purchase = __rand_timestamps(dataset_size, "2017-01-01", "2018-06-01")
    df["order_purchase_timestamp"] = purchase
    df["order_aproved_at"] = purchase + pd.to_timedelta(
        np.random.randint(1, 24, size=dataset_size), unit="h"
    )
    df["order_estimated_delivery_date"] = purchase + pd.to_timedelta(
        np.random.randint(10, 40, size=dataset_size), unit="D"
    )
    df["order_delivered_customer_date"] = purchase + pd.to_timedelta(
        np.random.randint(5, 45, size=dataset_size), unit="D"
    )

    df["customer_id"] = [f"cust_{i}" for i in range(dataset_size)]
    df["customer_city"] = "city"
    df["customer_state"] = np.random.choice(STATES, size=dataset_size)
    df["customer_zip_code_prefix"] = np.random.randint(
        100, 999, size=dataset_size
    ).astype(str)
    df["product_category_name_english"] = np.random.choice(
        CATEGORIES, size=dataset_size
    )
    df["product_name_lenght"] = np.random.randint(20, 80, size=dataset_size)
    df["product_description_lenght"] = np.random.randint(100, 2000, size=dataset_size)
    df["product_photos_qty"] = np.random.randint(1, 8, size=dataset_size)
    df["product_id"] = [f"prod_{i}" for i in range(dataset_size)]
    df["review_id"] = [f"rev_{i}" for i in range(dataset_size)]
    df["review_score"] = np.random.choice(
        [1, 2, 3, 4, 5], size=dataset_size, p=[0.10, 0.05, 0.10, 0.20, 0.55]
    )
    df["review_comment_title"] = ""
    df["review_comment_message"] = ""
    df["review_creation_date"] = purchase
    df["review_answer_timestamp"] = purchase
    return df


def generate_engineered_dataset(dataset_size: int = 100, seed: int = 42) -> pd.DataFrame:
    """Dataset with pre-computed engineered features.

    Does not depend on the `AttributesAdder` implementation – used in unit tests
    for `build_transformer` / `train_model`.
    """
    np.random.seed(seed)
    raw = generate_dataset(dataset_size=dataset_size, seed=seed)
    df = raw.drop(
        columns=[
            "order_purchase_timestamp",
            "order_aproved_at",
            "order_estimated_delivery_date",
            "order_delivered_customer_date",
        ]
    )
    df["wd_estimated_delivery_time"] = np.random.randint(5, 30, size=dataset_size)
    df["wd_actual_delivery_time"] = np.random.randint(3, 40, size=dataset_size)
    df["wd_delivery_time_delta"] = (
        df["wd_actual_delivery_time"] - df["wd_estimated_delivery_time"]
    )
    df["is_late"] = (df["wd_delivery_time_delta"] > 0).astype(int)
    df["average_product_value"] = df["order_products_value"] / df["order_items_qty"]
    df["total_order_value"] = df["order_products_value"] + df["order_freight_value"]
    df["order_freight_ratio"] = df["order_freight_value"] / df["order_products_value"]
    df["purchase_dayofweek"] = np.random.randint(0, 7, size=dataset_size)
    return df
