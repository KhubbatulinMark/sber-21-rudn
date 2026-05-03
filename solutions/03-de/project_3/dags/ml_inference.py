import pickle
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
from airflow.decorators import dag, task
from airflow.operators.python import ShortCircuitOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook

from _common import DEFAULT_ARGS
from include.drift.sql import CATEGORICAL_FEATURES, NUMERICAL_FEATURES
from include.ml.datasets import MODEL_DATASET

ARTEFACTS = Path("/opt/airflow/artefacts")
LATEST = ARTEFACTS / "latest"

INFERENCE_SQL = """
SELECT fs.order_id, fs.price, fs.freight_value, fs.revenue,
       dp.product_category_name_english
FROM analytics.facts_sales fs
JOIN analytics.dim_products dp ON dp.product_key = fs.product_key
WHERE fs.order_purchase_timestamp >= %(window_start)s
  AND fs.order_purchase_timestamp <  %(window_end)s
"""


@dag(
    dag_id="ml_inference",
    schedule=[MODEL_DATASET],
    start_date=datetime(2024, 1, 1),
    catchup=False,
    default_args=DEFAULT_ARGS,
    tags=["olist", "ml"],
)
def ml_inference():
    def _extract(**context) -> bool:
        ds = context["ds"]
        out_dir = ARTEFACTS / ds
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / "inference_input.parquet"

        window_end = context["data_interval_end"]
        window_start = context["data_interval_start"]
        if window_start == window_end:
            window_start = window_end - timedelta(days=1)
        conn = PostgresHook(postgres_conn_id="postgres_warehouse").get_conn()
        try:
            df = pd.read_sql(
                INFERENCE_SQL, conn,
                params={"window_start": window_start, "window_end": window_end},
            )
            if df.empty:
                df = pd.read_sql(
                    INFERENCE_SQL, conn,
                    params={
                        "window_start": window_end - timedelta(days=365),
                        "window_end": window_end,
                    },
                )
        finally:
            conn.close()
        if df.empty:
            return False
        df.to_parquet(out_path, index=False)
        context["ti"].xcom_push(key="input_path", value=str(out_path))
        context["ti"].xcom_push(key="row_count", value=len(df))
        return True

    extract_recent_orders = ShortCircuitOperator(
        task_id="extract_recent_orders", python_callable=_extract
    )

    @task()
    def run_inference(**context) -> str:
        input_path = Path(context["ti"].xcom_pull(
            task_ids="extract_recent_orders", key="input_path"
        ))
        df = pd.read_parquet(input_path)
        transformer = pickle.loads((LATEST / "transformer.pkl").read_bytes())
        model = pickle.loads((LATEST / "model.pkl").read_bytes())

        X = df[NUMERICAL_FEATURES + CATEGORICAL_FEATURES]
        preds = np.clip(model.predict(transformer.transform(X)), 1.0, 5.0)
        out = df[["order_id"]].assign(predicted_review_score=preds)

        out_path = input_path.with_name("predictions.parquet")
        out.to_parquet(out_path, index=False)
        return str(out_path)

    @task()
    def write_predictions(predictions_path: str) -> int:
        df = pd.read_parquet(predictions_path)
        model_name = LATEST.resolve().name
        rows = [(r.order_id, model_name, float(r.predicted_review_score))
                for r in df.itertuples(index=False)]
        PostgresHook(postgres_conn_id="postgres_warehouse").insert_rows(
            table="analytics.predictions",
            rows=rows,
            target_fields=["order_id", "model_name", "predicted_review_score"],
        )
        return len(rows)

    @task()
    def validate_predictions(written: int, **context) -> None:
        expected = context["ti"].xcom_pull(
            task_ids="extract_recent_orders", key="row_count"
        )
        assert written == expected, f"written={written}, expected={expected}"

    preds = run_inference()
    written = write_predictions(preds)
    extract_recent_orders >> preds
    validate_predictions(written)


ml_inference()
