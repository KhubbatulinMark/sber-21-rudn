from typing import Any
from dataclasses import dataclass, field


@dataclass
class GBRConfig:
    _target_: str = field(default="sklearn.ensemble.GradientBoostingRegressor")
    n_estimators: int = field(default=100)
    max_depth: int = field(default=3)
    learning_rate: float = field(default=0.1)
    random_state: int = field(default=42)


@dataclass
class LinRegConfig:
    _target_: str = field(default="sklearn.linear_model.LinearRegression")
    fit_intercept: bool = field(default=True)


@dataclass
class ModelConfig:
    model_name: str
    model_params: Any
