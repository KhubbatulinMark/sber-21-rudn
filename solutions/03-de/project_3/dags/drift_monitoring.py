import json
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
from airflow.decorators import dag, task
from airflow.operators.empty import EmptyOperator
from airflow.operators.python import BranchPythonOperator
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.utils.trigger_rule import TriggerRule

from _common import DEFAULT_ARGS
from include.alerts.telegram import notify_text
from include.drift.report import build_drift_report, parse_drift_summary
from include.drift.sql import FEATURES_SQL
from include.drift.tests import run_test_suite
from include.etl.load import apply_ddl

ARTEFACTS = Path("/opt/airflow/artefacts")
DRIFT_DIR = ARTEFACTS / "drift"
REFERENCE_PATH = DRIFT_DIR / "reference.parquet"
WINDOW_DAYS = 7


@dag(
    dag_id="drift_monitoring",
    schedule="@weekly",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    default_args=DEFAULT_ARGS,
    tags=["olist", "drift"],
)
def drift_monitoring():
    @task()
    def apply_drift_ddl() -> None:
        apply_ddl("postgres_warehouse", "drift.sql")

    @task()
    def ensure_reference() -> str:
        DRIFT_DIR.mkdir(parents=True, exist_ok=True)
        if not REFERENCE_PATH.exists():
            conn = PostgresHook(postgres_conn_id="postgres_warehouse").get_conn()
            try:
                pd.read_sql(FEATURES_SQL, conn).to_parquet(REFERENCE_PATH, index=False)
            finally:
                conn.close()
        return str(REFERENCE_PATH)

    @task()
    def extract_current(**context) -> str:
        ds = context["ds"]
        out_path = DRIFT_DIR / f"current_{ds}.parquet"
        window_end = context["data_interval_end"]
        window_start = window_end - timedelta(days=WINDOW_DAYS)
        conn = PostgresHook(postgres_conn_id="postgres_warehouse").get_conn()
        sql = FEATURES_SQL + (
            " AND fs.order_purchase_timestamp >= %(window_start)s"
            " AND fs.order_purchase_timestamp <  %(window_end)s"
        )
        try:
            df = pd.read_sql(
                sql, conn,
                params={"window_start": window_start, "window_end": window_end},
            )
            if df.empty:
                df = pd.read_sql(FEATURES_SQL, conn)
        finally:
            conn.close()
        df.to_parquet(out_path, index=False)
        context["ti"].xcom_push(key="window_start", value=window_start.date().isoformat())
        context["ti"].xcom_push(key="window_end", value=window_end.date().isoformat())
        return str(out_path)

    @task()
    def build_report(reference_path: str, current_path: str) -> dict:
        html_path, json_path = build_drift_report(
            Path(reference_path), Path(current_path), DRIFT_DIR
        )
        return {"html_path": str(html_path), "json_path": str(json_path)}

    @task()
    def persist_metrics(report: dict, **context) -> None:
        summary = parse_drift_summary(Path(report["json_path"]))
        ti = context["ti"]
        PostgresHook(postgres_conn_id="postgres_warehouse").insert_rows(
            table="analytics.drift_metrics",
            rows=[(
                datetime.utcnow(),
                ti.xcom_pull(task_ids="extract_current", key="window_start"),
                ti.xcom_pull(task_ids="extract_current", key="window_end"),
                summary["share_of_drifted_columns"],
                summary["dataset_drift"],
                summary["n_drifted_features"],
                summary["n_features"],
                report["html_path"],
            )],
            target_fields=[
                "run_ts", "window_start", "window_end",
                "share_of_drifted_columns", "dataset_drift",
                "n_drifted_features", "n_features", "report_path",
            ],
        )

    @task()
    def run_tests(reference_path: str, current_path: str) -> dict:
        return run_test_suite(Path(reference_path), Path(current_path))

    def _decide(**context) -> str:
        result = context["ti"].xcom_pull(task_ids="run_tests")
        return "no_action" if result["all_passed"] else "react"

    decide_action = BranchPythonOperator(
        task_id="decide_action", python_callable=_decide
    )
    no_action = EmptyOperator(task_id="no_action")
    react = EmptyOperator(task_id="react")

    trigger_retraining = TriggerDagRunOperator(
        task_id="trigger_retraining",
        trigger_dag_id="ml_training",
        wait_for_completion=False,
        reset_dag_run=True,
    )

    @task()
    def notify_telegram(report: dict, **context) -> None:
        result = context["ti"].xcom_pull(task_ids="run_tests")
        failed = ", ".join(t["name"] for t in result["failed"])
        notify_text(
            f"⚠️ drift detected\nfailed tests: {failed}\nreport: {report['html_path']}"
        )

    @task(trigger_rule=TriggerRule.ALL_DONE)
    def log_incident(report: dict, **context) -> None:
        result = context["ti"].xcom_pull(task_ids="run_tests")
        if result is None or result.get("all_passed"):
            return
        triggered = context["ti"].xcom_pull(
            task_ids="trigger_retraining", key="trigger_run_id"
        )
        PostgresHook(postgres_conn_id="postgres_warehouse").insert_rows(
            table="analytics.drift_incidents",
            rows=[(
                datetime.utcnow(),
                json.dumps(result["failed"]),
                report["html_path"],
                triggered,
            )],
            target_fields=["run_ts", "failed_tests", "report_path", "triggered_dag_run_id"],
        )

    ddl = apply_drift_ddl()
    ref = ensure_reference()
    cur = extract_current()
    ddl >> [ref, cur]

    report = build_report(ref, cur)
    persist_metrics(report)

    tests = run_tests(ref, cur)
    tests >> decide_action >> [no_action, react]
    react >> [trigger_retraining, notify_telegram(report), log_incident(report)]


drift_monitoring()
