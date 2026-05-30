from pathlib import Path

from airflow.providers.postgres.hooks.postgres import PostgresHook

DDL_DIR = Path("/opt/airflow/include/ddl")
DATASETS_DIR = Path("/opt/airflow/datasets")

CSV_TO_TABLE = {
    "olist_orders_dataset.csv": ("postgres_sales", "orders"),
    "olist_order_items_dataset.csv": ("postgres_sales", "order_items"),
    "olist_products_dataset.csv": ("postgres_catalog", "products"),
    "product_category_name_translation.csv": ("postgres_catalog", "category_translation"),
    "olist_order_reviews_dataset.csv": ("postgres_catalog", "reviews"),
}

DATE_COLUMN = {
    "orders": "order_purchase_timestamp",
    "order_items": "shipping_limit_date",
    "reviews": "review_creation_date",
}


def apply_ddl(conn_id: str, sql_filename: str) -> None:
    sql_text = (DDL_DIR / sql_filename).read_text()
    PostgresHook(postgres_conn_id=conn_id).run(sql_text)


def _stage_table_columns(hook: PostgresHook, table: str) -> list[str]:
    rows = hook.get_records(
        """
        SELECT column_name FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = %s
              AND is_generated = 'NEVER' AND is_identity = 'NO'
        ORDER BY ordinal_position
        """,
        parameters=(table,),
    )
    return [r[0] for r in rows]


def copy_csv_to_table(csv_filename: str, mode: str = "full", since: str | None = None) -> int:
    conn_id, table = CSV_TO_TABLE[csv_filename]
    csv_path = DATASETS_DIR / csv_filename
    hook = PostgresHook(postgres_conn_id=conn_id)
    cols = _stage_table_columns(hook, table)
    cols_sql = ", ".join(cols)

    conn = hook.get_conn()
    try:
        with conn.cursor() as cur:
            if mode == "full":
                cur.execute(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE")
                with csv_path.open("r") as f:
                    cur.copy_expert(
                        f"COPY {table} ({cols_sql}) FROM STDIN WITH (FORMAT CSV, HEADER TRUE)", f
                    )
                rowcount = cur.rowcount
            else:
                stage = f"{table}_stage"
                cur.execute(f"CREATE TEMP TABLE {stage} (LIKE {table} INCLUDING DEFAULTS)")
                with csv_path.open("r") as f:
                    cur.copy_expert(
                        f"COPY {stage} ({cols_sql}) FROM STDIN WITH (FORMAT CSV, HEADER TRUE)", f
                    )
                date_col = DATE_COLUMN.get(table)
                if date_col and since:
                    cur.execute(
                        f"INSERT INTO {table} ({cols_sql}) "
                        f"SELECT {cols_sql} FROM {stage} WHERE {date_col} >= %s "
                        f"ON CONFLICT DO NOTHING",
                        (since,),
                    )
                else:
                    cur.execute(
                        f"INSERT INTO {table} ({cols_sql}) "
                        f"SELECT {cols_sql} FROM {stage} ON CONFLICT DO NOTHING"
                    )
                rowcount = cur.rowcount
        conn.commit()
    finally:
        conn.close()

    return rowcount
