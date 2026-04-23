import psycopg
from psycopg.rows import dict_row

from db_setup import get_conn_catalog, get_conn_sales, get_conn_warehouse

STAGING_DDL = """
CREATE TABLE IF NOT EXISTS staging.orders (
    order_id                        TEXT,
    customer_id                     TEXT,
    order_status                    TEXT,
    order_purchase_timestamp        TIMESTAMP,
    order_approved_at               TIMESTAMP,
    order_delivered_carrier_date    TIMESTAMP,
    order_delivered_customer_date   TIMESTAMP,
    order_estimated_delivery_date   TIMESTAMP
);

CREATE TABLE IF NOT EXISTS staging.order_items (
    order_id            TEXT,
    order_item_id       INTEGER,
    product_id          TEXT,
    seller_id           TEXT,
    shipping_limit_date TIMESTAMP,
    price               NUMERIC(10, 2),
    freight_value       NUMERIC(10, 2)
);

CREATE TABLE IF NOT EXISTS staging.products (
    product_id                  TEXT,
    product_category_name       TEXT,
    product_name_lenght         INTEGER,
    product_description_lenght  INTEGER,
    product_photos_qty          INTEGER,
    product_weight_g            INTEGER,
    product_length_cm           INTEGER,
    product_height_cm           INTEGER,
    product_width_cm            INTEGER
);

CREATE TABLE IF NOT EXISTS staging.category_translation (
    product_category_name           TEXT,
    product_category_name_english   TEXT
);

CREATE TABLE IF NOT EXISTS staging.reviews (
    review_key              BIGINT,
    review_id               TEXT,
    order_id                TEXT,
    review_score            INTEGER,
    review_comment_title    TEXT,
    review_comment_message  TEXT,
    review_creation_date    TIMESTAMP,
    review_answer_timestamp TIMESTAMP
);
"""


def _read_table(conn: psycopg.Connection, table: str) -> list[dict]:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(f"SELECT * FROM {table}")
        return cur.fetchall()


def _bulk_insert(cur: psycopg.Cursor, table: str, rows: list[dict]) -> None:
    if not rows:
        return
    columns = list(rows[0].keys())
    placeholders = ", ".join(f"%({c})s" for c in columns)
    col_list = ", ".join(columns)
    cur.executemany(
        f"INSERT INTO {table} ({col_list}) VALUES ({placeholders})",
        rows,
    )


def build_staging() -> None:
    with get_conn_warehouse() as wh_conn:
        with wh_conn.cursor() as cur:
            cur.execute("CREATE SCHEMA IF NOT EXISTS staging")
            cur.execute("CREATE SCHEMA IF NOT EXISTS analytics")
            cur.execute(STAGING_DDL)
        wh_conn.commit()

        sales_tables = {
            "orders": _read_table(get_conn_sales(), "orders"),
            "order_items": _read_table(get_conn_sales(), "order_items"),
        }
        catalog_tables = {
            "products": _read_table(get_conn_catalog(), "products"),
            "category_translation": _read_table(get_conn_catalog(), "category_translation"),
            "reviews": _read_table(get_conn_catalog(), "reviews"),
        }

        with wh_conn.cursor() as cur:
            for table, rows in {**sales_tables, **catalog_tables}.items():
                cur.execute(f"TRUNCATE staging.{table} RESTART IDENTITY")
                _bulk_insert(cur, f"staging.{table}", rows)
                cur.execute(f"SELECT COUNT(*) FROM staging.{table}")
                count = cur.fetchone()[0]
                print(f"staging.{table:<25} {count:>8} rows")
        wh_conn.commit()


def build_analytics() -> None:
    with get_conn_warehouse() as conn:
        with conn.cursor() as cur:
            cur.execute("DROP TABLE IF EXISTS analytics.facts_reviews CASCADE")
            cur.execute("DROP TABLE IF EXISTS analytics.facts_sales CASCADE")
            cur.execute("DROP TABLE IF EXISTS analytics.dim_products CASCADE")

            cur.execute("""
                CREATE TABLE analytics.dim_products (
                    product_key                     BIGSERIAL PRIMARY KEY,
                    product_id                      TEXT UNIQUE NOT NULL,
                    product_category_name           TEXT,
                    product_category_name_english   TEXT
                )
            """)
            cur.execute("""
                INSERT INTO analytics.dim_products
                    (product_id, product_category_name, product_category_name_english)
                SELECT DISTINCT
                    p.product_id,
                    p.product_category_name,
                    ct.product_category_name_english
                FROM staging.products p
                LEFT JOIN staging.category_translation ct
                    ON p.product_category_name = ct.product_category_name
            """)
            cur.execute("SELECT COUNT(*) FROM analytics.dim_products")
            print(f"dim_products:  {cur.fetchone()[0]} rows")

            cur.execute("""
                CREATE TABLE analytics.facts_sales (
                    sales_key                   BIGSERIAL PRIMARY KEY,
                    order_id                    TEXT,
                    order_item_id               INTEGER,
                    product_key                 BIGINT REFERENCES analytics.dim_products(product_key),
                    order_purchase_timestamp    TIMESTAMP,
                    price                       NUMERIC(12, 2),
                    freight_value               NUMERIC(12, 2),
                    revenue                     NUMERIC(14, 2)
                )
            """)
            cur.execute("""
                INSERT INTO analytics.facts_sales
                    (order_id, order_item_id, product_key,
                     order_purchase_timestamp, price, freight_value, revenue)
                SELECT
                    oi.order_id,
                    oi.order_item_id,
                    dp.product_key,
                    o.order_purchase_timestamp,
                    oi.price,
                    oi.freight_value,
                    oi.price + oi.freight_value
                FROM staging.order_items oi
                INNER JOIN staging.orders o  ON oi.order_id   = o.order_id
                INNER JOIN analytics.dim_products dp ON oi.product_id = dp.product_id
            """)
            cur.execute("SELECT COUNT(*) FROM analytics.facts_sales")
            print(f"facts_sales:   {cur.fetchone()[0]} rows")

            cur.execute("""
                CREATE TABLE analytics.facts_reviews (
                    review_key              BIGSERIAL PRIMARY KEY,
                    review_id               TEXT,
                    order_id                TEXT,
                    product_key             BIGINT REFERENCES analytics.dim_products(product_key),
                    review_score            INTEGER,
                    review_comment_message  TEXT,
                    review_creation_date    TIMESTAMP,
                    linked_to_product       BOOLEAN NOT NULL
                )
            """)
            cur.execute("""
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
                LEFT JOIN staging.order_items oi ON r.order_id = oi.order_id AND oi.order_item_id = 1
                LEFT JOIN analytics.dim_products dp ON oi.product_id = dp.product_id
            """)
            cur.execute("SELECT COUNT(*) FROM analytics.facts_reviews")
            print(f"facts_reviews: {cur.fetchone()[0]} rows")

            cur.execute("""
                SELECT COUNT(*)
                FROM analytics.facts_sales fs
                WHERE NOT EXISTS (
                    SELECT 1 FROM analytics.dim_products dp
                    WHERE dp.product_key = fs.product_key
                )
            """)
            orphans = cur.fetchone()[0]
            print(f"Orphan facts_sales rows: {orphans}")
            assert orphans == 0, "Обнаружены осиротевшие факты в facts_sales!"

        conn.commit()


if __name__ == "__main__":
    build_staging()
    build_analytics()
