from functools import lru_cache
from typing import List

import numpy as np
import pandas as pd

from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from workalendar.america import Brazil


BR_CAL = Brazil()


@lru_cache(maxsize=None)
def _cached_working_days(start, end) -> int:
    return BR_CAL.get_working_days_delta(start, end)


def _working_days(start, end) -> int:
    if pd.isnull(start) or pd.isnull(end):
        return 0
    return _cached_working_days(pd.Timestamp(start).date(), pd.Timestamp(end).date())


class AttributesAdder(BaseEstimator, TransformerMixin):
    """Feature engineering based on hypotheses from the EDA notebook."""

    def fit(self, x: pd.DataFrame, y=None):
        return self

    def transform(self, x: pd.DataFrame, y=None) -> pd.DataFrame:
        df = x.copy()

        df["wd_estimated_delivery_time"] = df.apply(
            lambda r: _working_days(
                r["order_aproved_at"], r["order_estimated_delivery_date"]
            ),
            axis=1,
        )
        df["wd_actual_delivery_time"] = df.apply(
            lambda r: _working_days(
                r["order_aproved_at"], r["order_delivered_customer_date"]
            ),
            axis=1,
        )
        df["wd_delivery_time_delta"] = (
            df["wd_actual_delivery_time"] - df["wd_estimated_delivery_time"]
        )
        df["is_late"] = (
            df["order_delivered_customer_date"] > df["order_estimated_delivery_date"]
        ).astype(int)
        df["average_product_value"] = df["order_products_value"] / df[
            "order_items_qty"
        ].replace(0, np.nan)
        df["total_order_value"] = df["order_products_value"] + df["order_freight_value"]
        df["order_freight_ratio"] = df["order_freight_value"] / df[
            "order_products_value"
        ].replace(0, np.nan)
        df["purchase_dayofweek"] = df["order_purchase_timestamp"].dt.dayofweek

        df = df.drop(
            columns=[
                "order_purchase_timestamp",
                "order_aproved_at",
                "order_estimated_delivery_date",
                "order_delivered_customer_date",
            ],
            errors="ignore",
        )
        return df


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    return AttributesAdder().transform(df)


class TargetEncoder(BaseEstimator, TransformerMixin):
    """Mean target encoder with smoothing."""

    def __init__(self, smoothing: float = 10.0):
        self.smoothing = smoothing
        self.global_mean_: float = 0.0
        self.mappings_: dict = {}

    def fit(self, x: pd.DataFrame, y: pd.Series):
        x = pd.DataFrame(x).reset_index(drop=True)
        y = pd.Series(y).reset_index(drop=True)
        self.global_mean_ = float(y.mean())
        self.mappings_ = {}
        for col in x.columns:
            agg = y.groupby(x[col]).agg(["mean", "count"])
            smoothed = (
                agg["mean"] * agg["count"] + self.global_mean_ * self.smoothing
            ) / (agg["count"] + self.smoothing)
            self.mappings_[col] = smoothed.to_dict()
        return self

    def transform(self, x: pd.DataFrame) -> pd.DataFrame:
        x = pd.DataFrame(x).copy()
        for col in x.columns:
            x[col] = x[col].map(self.mappings_.get(col, {})).fillna(self.global_mean_)
        return x


def process_categorical_features(categorical_df: pd.DataFrame) -> pd.DataFrame:
    categorical_pipeline = build_categorical_pipeline()
    transformed = categorical_pipeline.fit_transform(categorical_df)
    if hasattr(transformed, "toarray"):
        transformed = transformed.toarray()
    return pd.DataFrame(transformed)


def build_categorical_pipeline(encoder: str = "onehot") -> Pipeline:
    if encoder == "onehot":
        final_step = ("ohe", OneHotEncoder(handle_unknown="ignore"))
    elif encoder == "target":
        final_step = ("target", TargetEncoder())
    else:
        raise ValueError(f"Unknown categorical encoder: {encoder!r}")
    return Pipeline(
        [
            ("imputer", SimpleImputer(strategy="most_frequent")),
            final_step,
        ]
    )


def process_numerical_features(numerical_df: pd.DataFrame) -> pd.DataFrame:
    num_pipeline = build_numerical_pipeline()
    return pd.DataFrame(num_pipeline.fit_transform(numerical_df))


def build_numerical_pipeline() -> Pipeline:
    return Pipeline(
        [
            ("outlier_remover", OutlierRemover()),
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler(with_mean=False)),
        ]
    )


def make_features(transformer: ColumnTransformer, df: pd.DataFrame) -> pd.DataFrame:
    transformed = transformer.transform(df)
    if hasattr(transformed, "toarray"):
        transformed = transformed.toarray()
    return pd.DataFrame(transformed)


def extract_target(df: pd.DataFrame, target_col: str) -> pd.Series:
    return df[target_col].values


class OutlierRemover(BaseEstimator, TransformerMixin):
    def __init__(self, factor: float = 1.5):
        self.factor = factor

    def outlier_removal(self, x: pd.Series) -> pd.Series:
        x = pd.Series(x).copy()
        q1 = x.quantile(0.25)
        q3 = x.quantile(0.75)
        iqr = q3 - q1
        lower_bound = q1 - (self.factor * iqr)
        upper_bound = q3 + (self.factor * iqr)
        x.loc[((x < lower_bound) | (x > upper_bound))] = np.nan
        return x

    def fit(self, x, y=None):
        return self

    def transform(self, x):
        return pd.DataFrame(x).apply(self.outlier_removal)


def build_transformer(
    categorical_features: List[str],
    numerical_features: List[str],
    categorical_encoder: str = "onehot",
) -> ColumnTransformer:
    return ColumnTransformer(
        [
            (
                "categorical_pipeline",
                build_categorical_pipeline(categorical_encoder),
                list(categorical_features),
            ),
            (
                "numerical_pipeline",
                build_numerical_pipeline(),
                list(numerical_features),
            ),
        ]
    )
