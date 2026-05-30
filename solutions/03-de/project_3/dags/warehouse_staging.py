from datetime import datetime

from airflow.decorators import dag, task
from airflow.exceptions import AirflowSkipException
from airflow.operators.empty import EmptyOperator
from airflow.operators.python import BranchPythonOperator
from airflow.sensors.external_task import ExternalTaskSensor
from airflow.utils.task_group import TaskGroup
from airflow.utils.trigger_rule import TriggerRule

from _common import DEFAULT_ARGS
from include.alerts.telegram import notify_text
from include.etl.load import apply_ddl
from include.warehouse.staging import EXPECTED_ROWS, load_staging

THRESHOLD = 0.5


@dag(
    dag_id="warehouse_staging",
    schedule=None,
    start_date=datetime(2024, 1, 1),
    catchup=False,
    default_args=DEFAULT_ARGS,
    tags=["olist", "warehouse"],
)
def warehouse_staging():
    wait_for_ingest = ExternalTaskSensor(
        task_id="wait_for_ingest",
        external_dag_id="olist_ingest",
        external_task_id=None,
        mode="reschedule",
        poke_interval=30,
        timeout=1800,
        allowed_states=["success"],
        execution_date_fn=lambda dt: dt.replace(hour=0, minute=0, second=0, microsecond=0),
    )

    @task()
    def apply_warehouse_ddl() -> None:
        apply_ddl("postgres_warehouse", "warehouse.sql")

    def _stage(table: str):
        @task(task_id=f"stg_{table}")
        def _t(t=table) -> int:
            return load_staging(t)
        return _t()

    with TaskGroup("tg_staging") as tg_staging:
        for table in EXPECTED_ROWS:
            _stage(table)

    def _branch_check(**context) -> str:
        ti = context["ti"]
        for table, expected in EXPECTED_ROWS.items():
            count = ti.xcom_pull(task_ids=f"tg_staging.stg_{table}")
            if count is None or count < expected * THRESHOLD:
                ti.xcom_push(key="failed_table", value=f"{table}: {count}/{expected}")
                return "alert_and_skip"
        return "proceed"

    check_row_counts = BranchPythonOperator(
        task_id="check_row_counts", python_callable=_branch_check
    )

    @task()
    def alert_and_skip(**context) -> None:
        failed = context["ti"].xcom_pull(task_ids="check_row_counts", key="failed_table")
        notify_text(f"⚠️ staging row-counts below threshold ({failed})")
        raise AirflowSkipException(f"row-count below threshold: {failed}")

    proceed = EmptyOperator(task_id="proceed")

    @task(trigger_rule=TriggerRule.NONE_FAILED_MIN_ONE_SUCCESS)
    def validate_staging(**context) -> None:
        ti = context["ti"]
        for table, expected in EXPECTED_ROWS.items():
            count = ti.xcom_pull(task_ids=f"tg_staging.stg_{table}")
            assert count == expected, f"{table}: {count} != {expected}"

    apply_ddl_t = apply_warehouse_ddl()
    skip_branch = alert_and_skip()
    validator = validate_staging()

    wait_for_ingest >> apply_ddl_t >> tg_staging >> check_row_counts
    check_row_counts >> [skip_branch, proceed]
    proceed >> validator


warehouse_staging()
