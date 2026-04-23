import json
import logging
import os

import hydra
import mlflow
import numpy as np
import pandas as pd
from omegaconf import OmegaConf
from sklearn.metrics import make_scorer, roc_auc_score
from sklearn.model_selection import cross_val_score

from satisfaction.entities import TrainingPipelineConfig
from satisfaction.data import read_data, split_train_test_data
from satisfaction.data.make_dataset import drop_unused_columns
from satisfaction.features import (
    build_transformer,
    engineer_features,
    extract_target,
    make_features,
)
from satisfaction.models import (
    train_model,
    serialize_model,
    predict_model,
    evaluate_model,
)

logger = logging.getLogger(__name__)


def prepare_val_features_for_predict(
    train_features: pd.DataFrame, val_features: pd.DataFrame
) -> pd.DataFrame:
    train_features, val_features = train_features.align(
        val_features, join="left", axis=1
    )
    return val_features.fillna(0)


def _binary_target(y, threshold: int = 4) -> np.ndarray:
    return (np.asarray(y).ravel() >= threshold).astype(int)


def _flatten_params(cfg_section: dict, prefix: str) -> dict:
    return {f"{prefix}.{k}": v for k, v in cfg_section.items()}


def train_pipeline(params: TrainingPipelineConfig) -> None:
    logger.info("Starting pipeline")

    tracking_uri = os.environ.get("MLFLOW_TRACKING_URI", "http://localhost:5000")
    experiment = os.environ.get("MLFLOW_EXPERIMENT", "satisfaction")
    mlflow.set_tracking_uri(tracking_uri)
    mlflow.set_experiment(experiment)
    logger.info(f"mlflow tracking: {tracking_uri} / experiment={experiment}")

    with mlflow.start_run(run_name=params.model.model_name):
        mlflow.log_params(
            _flatten_params(OmegaConf.to_container(params.model.model_params), "model")
        )
        mlflow.log_param("model.name", params.model.model_name)
        mlflow.log_param("split.test_size", params.split.test_size)
        mlflow.log_param("split.random_state", params.split.random_state)
        mlflow.log_param("feature.categorical_encoder", params.feature.categorical_encoder)

        data = read_data(params.dataset.input_data_path)
        logger.info(f"data.shape is {data.shape}")

        data = drop_unused_columns(data, params.feature.features_to_drop)
        data = engineer_features(data)
        logger.info(f"data.shape after feature engineering is {data.shape}")

        train_df, test_df = split_train_test_data(
            data,
            target_col=params.feature.target_col,
            test_size=params.split.test_size,
            random_state=params.split.random_state,
        )
        logger.info(f"train size: {len(train_df)}, test size: {len(test_df)}")

        transformer = build_transformer(
            categorical_features=params.feature.categorical_features,
            numerical_features=params.feature.numerical_features,
            categorical_encoder=params.feature.categorical_encoder,
        )
        train_target = extract_target(train_df, params.feature.target_col)
        transformer.fit(train_df, train_target)
        train_features = make_features(transformer, train_df)
        logger.info(f"train_features.shape is {train_features.shape}")

        try:
            from hydra.utils import instantiate

            cv_model = instantiate(params.model.model_params)
            cv_scorer = make_scorer(roc_auc_score, response_method="predict")
            cv_scores = cross_val_score(
                cv_model,
                train_features,
                _binary_target(train_target),
                cv=3,
                scoring=cv_scorer,
            )
            cv_mean, cv_std = float(cv_scores.mean()), float(cv_scores.std())
            logger.info(f"cv roc_auc mean={cv_mean:.4f} std={cv_std:.4f}")
            mlflow.log_metric("cv_roc_auc_mean", cv_mean)
            mlflow.log_metric("cv_roc_auc_std", cv_std)
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"cross_val_score failed: {exc}")

        model = train_model(params.model.model_params, train_features, train_target)

        test_features = make_features(transformer, test_df)
        test_target = extract_target(test_df, params.feature.target_col)
        val_features_prepared = prepare_val_features_for_predict(
            train_features, test_features
        )
        logger.info(f"test_features.shape is {val_features_prepared.shape}")

        predicts = predict_model(model, val_features_prepared)
        metrics = evaluate_model(predicts, test_target)
        logger.info(f"metrics: {metrics}")
        mlflow.log_metrics(metrics)

        metrics_dir = os.path.join(os.getcwd(), "metrics")
        models_dir = os.path.join(os.getcwd(), "models")
        os.makedirs(metrics_dir, exist_ok=True)
        os.makedirs(models_dir, exist_ok=True)

        metrics_path = os.path.join(metrics_dir, f"{params.model.model_name}.json")
        with open(metrics_path, "w") as f:
            json.dump(metrics, f)
        logger.info(f"metrics saved to {metrics_path}")

        model_path = os.path.join(models_dir, f"{params.model.model_name}.pkl")
        serialize_model(model, model_path)
        logger.info(f"model saved to {model_path}")

        transformer_path = os.path.join(models_dir, "transformer.pkl")
        serialize_model(transformer, transformer_path)
        logger.info(f"transformer saved to {transformer_path}")

        mlflow.log_artifact(metrics_path, artifact_path="metrics")
        mlflow.log_artifact(model_path, artifact_path="models")
        mlflow.log_artifact(transformer_path, artifact_path="models")
        logger.info("artefacts logged to mlflow")

    logger.info("Finish train")


@hydra.main(config_path="../configs", config_name="config", version_base=None)
def main(cfg: TrainingPipelineConfig) -> None:
    train_pipeline(cfg)


if __name__ == "__main__":
    main()
