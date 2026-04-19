import os

import psycopg
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL_SALES = os.environ["DATABASE_URL_SALES"]
DATABASE_URL_CATALOG = os.environ["DATABASE_URL_CATALOG"]
DATABASE_URL_WAREHOUSE = os.environ["DATABASE_URL_WAREHOUSE"]


def get_conn_sales() -> psycopg.Connection:
    return psycopg.connect(DATABASE_URL_SALES)


def get_conn_catalog() -> psycopg.Connection:
    return psycopg.connect(DATABASE_URL_CATALOG)


def get_conn_warehouse() -> psycopg.Connection:
    return psycopg.connect(DATABASE_URL_WAREHOUSE)


def create_tables() -> None:
    with get_conn_sales() as conn:
        with conn.cursor() as cur:
            cur.execute("DROP TABLE IF EXISTS order_items CASCADE")
            cur.execute("DROP TABLE IF EXISTS orders CASCADE")
            cur.execute("""
                CREATE TABLE orders (
                    order_id                        TEXT PRIMARY KEY,
                    customer_id                     TEXT NOT NULL,
                    order_status                    TEXT,
                    order_purchase_timestamp        TIMESTAMP,
                    order_approved_at               TIMESTAMP,
                    order_delivered_carrier_date    TIMESTAMP,
                    order_delivered_customer_date   TIMESTAMP,
                    order_estimated_delivery_date   TIMESTAMP
                )
            """)
            cur.execute("""
                CREATE TABLE order_items (
                    order_id            TEXT,
                    order_item_id       INTEGER,
                    product_id          TEXT NOT NULL,
                    seller_id           TEXT,
                    shipping_limit_date TIMESTAMP,
                    price               NUMERIC(10, 2),
                    freight_value       NUMERIC(10, 2),
                    PRIMARY KEY (order_id, order_item_id)
                )
            """)
        conn.commit()
        print("db_sales: tables created")

    with get_conn_catalog() as conn:
        with conn.cursor() as cur:
            cur.execute("DROP TABLE IF EXISTS reviews CASCADE")
            cur.execute("DROP TABLE IF EXISTS category_translation CASCADE")
            cur.execute("DROP TABLE IF EXISTS products CASCADE")
            cur.execute("""
                CREATE TABLE products (
                    product_id                  TEXT PRIMARY KEY,
                    product_category_name       TEXT,
                    product_name_lenght         INTEGER,
                    product_description_lenght  INTEGER,
                    product_photos_qty          INTEGER,
                    product_weight_g            INTEGER,
                    product_length_cm           INTEGER,
                    product_height_cm           INTEGER,
                    product_width_cm            INTEGER
                )
            """)
            cur.execute("""
                CREATE TABLE category_translation (
                    product_category_name           TEXT PRIMARY KEY,
                    product_category_name_english   TEXT
                )
            """)
            cur.execute("""
                CREATE TABLE reviews (
                    review_key              BIGSERIAL PRIMARY KEY,
                    review_id               TEXT,
                    order_id                TEXT,
                    review_score            INTEGER,
                    review_comment_title    TEXT,
                    review_comment_message  TEXT,
                    review_creation_date    TIMESTAMP,
                    review_answer_timestamp TIMESTAMP
                )
            """)
        conn.commit()
        print("db_catalog: tables created")

    for db_name, get_conn in [("db_sales", get_conn_sales), ("db_catalog", get_conn_catalog)]:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                    ORDER BY table_name
                """)
                tables = [row[0] for row in cur.fetchall()]
            print(f"{db_name} tables: {tables}")


if __name__ == "__main__":
    for name, get_conn in [
        ("db_sales", get_conn_sales),
        ("db_catalog", get_conn_catalog),
        ("warehouse", get_conn_warehouse),
    ]:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
        print(f"{name:<12} OK")

    create_tables()
