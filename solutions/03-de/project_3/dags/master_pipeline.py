from datetime import datetime

from airflow.decorators import dag
from airflow.operators.trigger_dagrun import TriggerDagRunOperator

from _common import DEFAULT_ARGS


@dag(
    dag_id="master_pipeline",
    schedule="0 2 * * *",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    default_args=DEFAULT_ARGS,
    tags=["olist", "master"],
)
def master_pipeline():
    common = {
        "wait_for_completion": True,
        "poke_interval": 30,
        "failed_states": ["failed"],
        "allowed_states": ["success"],
        "logical_date": "{{ logical_date }}",
        "reset_dag_run": True,
    }
    trigger_ingest = TriggerDagRunOperator(
        task_id="trigger_ingest", trigger_dag_id="olist_ingest", **common
    )
    trigger_staging = TriggerDagRunOperator(
        task_id="trigger_staging", trigger_dag_id="warehouse_staging", **common
    )
    trigger_analytics = TriggerDagRunOperator(
        task_id="trigger_analytics", trigger_dag_id="warehouse_analytics", **common
    )
    trigger_inference = TriggerDagRunOperator(
        task_id="trigger_inference", trigger_dag_id="ml_inference", **common
    )

    trigger_ingest >> trigger_staging >> trigger_analytics >> trigger_inference


master_pipeline()
