import logging
from datetime import datetime

from airflow.decorators import dag, task
from airflow.operators.bash import BashOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook

log = logging.getLogger(__name__)


@dag(
    dag_id="hello_olist",
    schedule="@daily",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["olist", "intro"],
)
def hello_olist():
    say_hello = BashOperator(
        task_id="say_hello",
        bash_command='echo "Olist pipeline is alive at {{ ds }}"',
    )

    @task()
    def count_orders() -> int:
        hook = PostgresHook(postgres_conn_id="postgres_sales")
        try:
            count = hook.get_first("SELECT COUNT(*) FROM orders")[0]
        except Exception as exc:
            log.warning("orders table not ready: %s", exc)
            count = 0
        log.info("orders rowcount: %s", count)
        return count

    say_hello >> count_orders()


hello_olist()
