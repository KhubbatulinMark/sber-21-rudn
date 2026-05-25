from datetime import datetime
from pathlib import Path

import pandas as pd
from airflow.decorators import dag, task
from airflow.exceptions import AirflowFailException
from airflow.providers.postgres.hooks.postgres import PostgresHook

from _common import DEFAULT_ARGS
from include.drift.sql import FEATURES_SQL
from include.ml.datasets import MODEL_DATASET
from include.ml.training import train_model

ARTEFACTS = Path("/opt/airflow/artefacts")
QUALITY_GATE_THRESHOLD = 0.65


@dag(
    dag_id="ml_training",
    schedule="@weekly",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    default_args=DEFAULT_ARGS,
    tags=["olist", "ml"],
)
def ml_training():
    @task()
    def prepare_dataset(**context) -> str:
        ds = context["ds"]
        out_dir = ARTEFACTS / ds
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / "training.parquet"

        conn = PostgresHook(postgres_conn_id="postgres_warehouse").get_conn()
        try:
            df = pd.read_sql(FEATURES_SQL, conn)
        finally:
            conn.close()
        df.to_parquet(out_path, index=False)
        return str(out_path)

    @task()
    def train(model_name: str, data_path: str, **context) -> dict:
        out_dir = ARTEFACTS / context["ds"] / model_name
        metrics = train_model(Path(data_path), model_name, out_dir)
        metrics["artefact_dir"] = str(out_dir)
        return metrics

    @task(outlets=[MODEL_DATASET])
    def evaluate_quality_gate(lr_metrics: dict, gbr_metrics: dict) -> str:
        winner = max([lr_metrics, gbr_metrics], key=lambda m: m["roc_auc"])
        if winner["roc_auc"] < QUALITY_GATE_THRESHOLD:
            raise AirflowFailException(
                f"quality gate failed: best roc_auc={winner['roc_auc']:.3f}"
            )
        latest = ARTEFACTS / "latest"
        if latest.is_symlink() or latest.exists():
            latest.unlink()
        latest.symlink_to(Path(winner["artefact_dir"]))
        return winner["model_name"]

    data = prepare_dataset()
    lr = train.override(task_id="train_lr")("lr", data)
    gbr = train.override(task_id="train_gbr")("gbr", data)
    evaluate_quality_gate(lr, gbr)


ml_training()
