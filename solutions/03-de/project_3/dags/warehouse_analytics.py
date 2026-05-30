from datetime import datetime

from airflow.decorators import dag, task
from airflow.sensors.external_task import ExternalTaskSensor

from _common import DEFAULT_ARGS
from include.warehouse.analytics import (
    build_dim_products,
    build_facts_reviews,
    build_facts_sales,
    count_orphan_facts,
)


@dag(
    dag_id="warehouse_analytics",
    schedule=None,
    start_date=datetime(2024, 1, 1),
    catchup=False,
    default_args=DEFAULT_ARGS,
    tags=["olist", "warehouse"],
)
def warehouse_analytics():
    wait_for_staging = ExternalTaskSensor(
        task_id="wait_for_staging",
        external_dag_id="warehouse_staging",
        external_task_id=None,
        mode="reschedule",
        poke_interval=30,
        timeout=1800,
        allowed_states=["success"],
        execution_date_fn=lambda dt: dt.replace(hour=0, minute=0, second=0, microsecond=0),
    )

    @task()
    def dim_products() -> int:
        return build_dim_products()

    @task()
    def facts_sales() -> int:
        return build_facts_sales()

    @task()
    def facts_reviews() -> int:
        return build_facts_reviews()

    @task()
    def validate_analytics(dim_n: int, sales_n: int, reviews_n: int) -> None:
        assert dim_n == 32951, f"dim_products: {dim_n}"
        assert sales_n == 112650, f"facts_sales: {sales_n}"
        assert reviews_n == 99224, f"facts_reviews: {reviews_n}"
        orphans = count_orphan_facts()
        assert orphans == 0, f"orphan facts_sales rows: {orphans}"

    dim = dim_products()
    sales = facts_sales()
    reviews = facts_reviews()

    wait_for_staging >> dim >> [sales, reviews]
    validate_analytics(dim, sales, reviews)


warehouse_analytics()
