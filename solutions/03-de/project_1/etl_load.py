from pathlib import Path

import psycopg

from connect import get_connection_catalog, get_connection_sales

DATASETS = Path(__file__).resolve().parents[3] / "production" / "AI_Data_Engineering.Project_1.ID_1577979" / "datasets"


def load_all() -> None:
    with get_connection_sales() as conn:
        with conn.cursor() as cur:
            cur.execute("TRUNCATE order_items, orders RESTART IDENTITY CASCADE")
            for csv_file, table in [
                ("olist_orders_dataset.csv", "orders"),
                ("olist_order_items_dataset.csv", "order_items"),
            ]:
                path = DATASETS / csv_file
                with open(path, "r") as f:
                    with cur.copy(f"COPY {table} FROM STDIN WITH (FORMAT CSV, HEADER TRUE)") as copy:
                        copy.write(f.read())
                cur.execute(f"SELECT COUNT(*) FROM {table}")
                count = cur.fetchone()[0]
                print(f"db_sales.{table:<20} {count:>8} rows")
        conn.commit()

    with get_connection_catalog() as conn:
        with conn.cursor() as cur:
            cur.execute("TRUNCATE reviews, products, category_translation RESTART IDENTITY CASCADE")
            reviews_cols = (
                "review_id, order_id, review_score, review_comment_title, "
                "review_comment_message, review_creation_date, review_answer_timestamp"
            )
            for csv_file, table, cols in [
                ("olist_products_dataset.csv", "products", "*"),
                ("product_category_name_translation.csv", "category_translation", "*"),
                ("olist_order_reviews_dataset.csv", "reviews", reviews_cols),
            ]:
                path = DATASETS / csv_file
                col_clause = f"({cols})" if cols != "*" else ""
                with open(path, "r") as f:
                    with cur.copy(
                        f"COPY {table} {col_clause} FROM STDIN WITH (FORMAT CSV, HEADER TRUE)"
                    ) as copy:
                        copy.write(f.read())
                cur.execute(f"SELECT COUNT(*) FROM {table}")
                count = cur.fetchone()[0]
                print(f"db_catalog.{table:<20} {count:>8} rows")
        conn.commit()


if __name__ == "__main__":
    load_all()
