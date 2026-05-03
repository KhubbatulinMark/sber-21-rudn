from datetime import datetime

from airflow.decorators import dag, task
from airflow.models.param import Param
from airflow.sensors.filesystem import FileSensor
from airflow.utils.task_group import TaskGroup

from _common import DEFAULT_ARGS
from include.etl.load import CSV_TO_TABLE, apply_ddl, copy_csv_to_table


@dag(
    dag_id="olist_ingest",
    schedule="@daily",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    default_args=DEFAULT_ARGS,
    tags=["olist", "ingest"],
    params={
        "mode": Param("full", enum=["full", "incremental"]),
        "since": Param("1970-01-01T00:00:00", type="string", format="date-time"),
    },
)
def olist_ingest():
    wait_for_csv = FileSensor(
        task_id="wait_for_csv",
        fs_conn_id="fs_default",
        filepath="olist_orders_dataset.csv",
        mode="reschedule",
        poke_interval=30,
        timeout=600,
    )

    @task()
    def init_sales() -> None:
        apply_ddl("postgres_sales", "db_sales.sql")

    @task()
    def init_catalog() -> None:
        apply_ddl("postgres_catalog", "db_catalog.sql")

    def _load(csv_filename: str):
        @task(task_id=f"load_{CSV_TO_TABLE[csv_filename][1]}")
        def _t(csv=csv_filename, **context) -> int:
            params = context["params"]
            return copy_csv_to_table(csv, mode=params["mode"], since=params.get("since"))
        return _t()

    sales_init = init_sales()
    catalog_init = init_catalog()

    with TaskGroup("tg_sales") as tg_sales:
        _load("olist_orders_dataset.csv")
        _load("olist_order_items_dataset.csv")

    with TaskGroup("tg_catalog") as tg_catalog:
        _load("olist_products_dataset.csv")
        _load("product_category_name_translation.csv")
        _load("olist_order_reviews_dataset.csv")

    wait_for_csv >> sales_init >> tg_sales
    wait_for_csv >> catalog_init >> tg_catalog


olist_ingest()
