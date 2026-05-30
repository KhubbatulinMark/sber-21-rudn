import io

from airflow.providers.postgres.hooks.postgres import PostgresHook

EXPECTED_ROWS = {
    "orders": 99441,
    "order_items": 112650,
    "products": 32951,
    "category_translation": 71,
    "reviews": 99224,
}

SOURCE_CONN = {
    "orders": "postgres_sales",
    "order_items": "postgres_sales",
    "products": "postgres_catalog",
    "category_translation": "postgres_catalog",
    "reviews": "postgres_catalog",
}


def _data_columns(hook: PostgresHook, schema: str, table: str) -> list[str]:
    rows = hook.get_records(
        """
        SELECT column_name FROM information_schema.columns
        WHERE table_schema = %s AND table_name = %s
              AND is_generated = 'NEVER' AND is_identity = 'NO'
        ORDER BY ordinal_position
        """,
        parameters=(schema, table),
    )
    return [r[0] for r in rows]


def load_staging(table: str) -> int:
    """Stream source.public.<table> → warehouse.staging.<table> via COPY BINARY,
    excluding IDENTITY columns from both ends so the schemas line up."""
    src_hook = PostgresHook(postgres_conn_id=SOURCE_CONN[table])
    dst_hook = PostgresHook(postgres_conn_id="postgres_warehouse")
    cols = _data_columns(dst_hook, "staging", table)
    cols_sql = ", ".join(cols)

    src = src_hook.get_conn()
    dst = dst_hook.get_conn()
    try:
        with dst.cursor() as cur_dst:
            cur_dst.execute(f"TRUNCATE TABLE staging.{table} RESTART IDENTITY")

        buf = io.BytesIO()
        with src.cursor() as cur_src:
            cur_src.copy_expert(
                f"COPY (SELECT {cols_sql} FROM public.{table}) TO STDOUT WITH (FORMAT BINARY)",
                buf,
            )
        buf.seek(0)

        with dst.cursor() as cur_dst:
            cur_dst.copy_expert(
                f"COPY staging.{table} ({cols_sql}) FROM STDIN WITH (FORMAT BINARY)",
                buf,
            )
            cur_dst.execute(f"SELECT COUNT(*) FROM staging.{table}")
            count = cur_dst.fetchone()[0]
        dst.commit()
    finally:
        src.close()
        dst.close()

    return count
