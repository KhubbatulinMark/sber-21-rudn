from pathlib import Path

from psycopg.rows import dict_row

from connect import (
    get_connection_catalog,
    get_connection_sales,
    get_connection_warehouse,
)

_DDL_DIR = Path(__file__).resolve().parent / "ddl"

# (source connection factory, source table, staging table, columns to drop from source rows)
_STAGING_SOURCES = [
    (get_connection_sales, "orders", "staging.orders", ()),
    (get_connection_sales, "order_items", "staging.order_items", ()),
    (get_connection_catalog, "products", "staging.products", ()),
    (get_connection_catalog, "category_translation", "staging.category_translation", ()),
    # review_key is GENERATED ALWAYS AS IDENTITY in staging.reviews — нельзя INSERT'ить явно.
    (get_connection_catalog, "reviews", "staging.reviews", ("review_key",)),
]


def _apply_and_list(ddl_filename: str, schema: str) -> list[str]:
    sql_text = (_DDL_DIR / ddl_filename).read_text(encoding="utf-8")
    with get_connection_warehouse() as conn, conn.cursor() as cur:
        cur.execute(sql_text)
        cur.execute(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = %s ORDER BY table_name",
            (schema,),
        )
        return [row[0] for row in cur.fetchall()]


def create_staging_tables() -> list[str]:
    return _apply_and_list("staging.sql", "staging")


def create_analytics_tables() -> list[str]:
    return _apply_and_list("analytics.sql", "analytics")


_POPULATE_ANALYTICS_SQL = [
    (
        "analytics.dim_products",
        """
        INSERT INTO analytics.dim_products
            (product_id, product_category_name, product_category_name_english)
        SELECT DISTINCT
            p.product_id,
            p.product_category_name,
            ct.product_category_name_english
        FROM staging.products p
        LEFT JOIN staging.category_translation ct
            ON p.product_category_name = ct.product_category_name
        """,
    ),
    (
        "analytics.facts_sales",
        """
        INSERT INTO analytics.facts_sales
            (order_id, order_item_id, product_key,
             order_purchase_timestamp, price, freight_value)
        SELECT
            oi.order_id,
            oi.order_item_id,
            dp.product_key,
            o.order_purchase_timestamp,
            oi.price,
            oi.freight_value
        FROM staging.order_items oi
        INNER JOIN staging.orders o ON oi.order_id = o.order_id
        INNER JOIN analytics.dim_products dp ON oi.product_id = dp.product_id
        """,
    ),
    (
        "analytics.facts_reviews",
        """
        INSERT INTO analytics.facts_reviews
            (review_id, order_id, product_key, review_score,
             review_comment_message, review_creation_date, linked_to_product)
        SELECT
            r.review_id,
            r.order_id,
            dp.product_key,
            r.review_score,
            r.review_comment_message,
            r.review_creation_date,
            dp.product_key IS NOT NULL
        FROM staging.reviews r
        LEFT JOIN staging.order_items oi
            ON r.order_id = oi.order_id AND oi.order_item_id = 1
        LEFT JOIN analytics.dim_products dp ON oi.product_id = dp.product_id
        """,
    ),
]


def populate_analytics() -> dict[str, int]:
    counts: dict[str, int] = {}
    with get_connection_warehouse() as conn, conn.cursor() as cur:
        cur.execute(
            "TRUNCATE analytics.facts_reviews, analytics.facts_sales, "
            "analytics.dim_products RESTART IDENTITY CASCADE"
        )
        for table, sql in _POPULATE_ANALYTICS_SQL:
            cur.execute(sql)
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            counts[table] = cur.fetchone()[0]
        conn.commit()
    return counts


def load_staging() -> dict[str, int]:
    counts: dict[str, int] = {}
    with get_connection_warehouse() as wh_conn, wh_conn.cursor() as wh_cur:
        for src_factory, src_table, dst_table, drop_cols in _STAGING_SOURCES:
            with src_factory() as src_conn, src_conn.cursor(row_factory=dict_row) as src_cur:
                src_cur.execute(f"SELECT * FROM {src_table}")
                rows = src_cur.fetchall()

            for col in drop_cols:
                for row in rows:
                    row.pop(col, None)

            wh_cur.execute(f"TRUNCATE {dst_table} RESTART IDENTITY")
            if rows:
                columns = list(rows[0].keys())
                col_list = ", ".join(columns)
                placeholders = ", ".join(f"%({c})s" for c in columns)
                wh_cur.executemany(
                    f"INSERT INTO {dst_table} ({col_list}) VALUES ({placeholders})",
                    rows,
                )

            wh_cur.execute(f"SELECT COUNT(*) FROM {dst_table}")
            counts[dst_table] = wh_cur.fetchone()[0]
        wh_conn.commit()
    return counts


if __name__ == "__main__":
    result_dir = Path(__file__).resolve().parent / "result"
    result_dir.mkdir(parents=True, exist_ok=True)

    staging_tables = create_staging_tables()
    staging_counts = load_staging()
    staging_lines = [f"staging.sql: {', '.join(staging_tables)}"]
    for table, count in staging_counts.items():
        staging_lines.append(f"  {table:<35} {count:>7} rows")
    (result_dir / "staging_setup.txt").write_text(
        "\n".join(staging_lines) + "\n", encoding="utf-8"
    )

    analytics_tables = create_analytics_tables()
    analytics_counts = populate_analytics()
    analytics_lines = [f"analytics.sql: {', '.join(analytics_tables)}"]
    for table, count in analytics_counts.items():
        analytics_lines.append(f"  {table:<35} {count:>7} rows")
    (result_dir / "analytics_setup.txt").write_text(
        "\n".join(analytics_lines) + "\n", encoding="utf-8"
    )
