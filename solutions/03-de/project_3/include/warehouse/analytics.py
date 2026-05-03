from airflow.providers.postgres.hooks.postgres import PostgresHook


def _hook() -> PostgresHook:
    return PostgresHook(postgres_conn_id="postgres_warehouse")


def build_dim_products() -> int:
    sql = """
    TRUNCATE TABLE analytics.dim_products RESTART IDENTITY CASCADE;
    INSERT INTO analytics.dim_products
        (product_id, product_category_name, product_category_name_english)
    SELECT p.product_id, p.product_category_name, ct.product_category_name_english
    FROM staging.products p
    LEFT JOIN staging.category_translation ct USING (product_category_name);
    """
    hook = _hook()
    hook.run(sql)
    return hook.get_first("SELECT COUNT(*) FROM analytics.dim_products")[0]


def build_facts_sales() -> int:
    sql = """
    TRUNCATE TABLE analytics.facts_sales RESTART IDENTITY;
    INSERT INTO analytics.facts_sales
        (order_id, order_item_id, product_key, order_purchase_timestamp,
         price, freight_value, revenue)
    SELECT oi.order_id, oi.order_item_id, dp.product_key,
           o.order_purchase_timestamp, oi.price, oi.freight_value,
           oi.price + oi.freight_value
    FROM staging.order_items oi
    JOIN staging.orders o USING (order_id)
    JOIN analytics.dim_products dp USING (product_id);
    """
    hook = _hook()
    hook.run(sql)
    return hook.get_first("SELECT COUNT(*) FROM analytics.facts_sales")[0]


def build_facts_reviews() -> int:
    sql = """
    TRUNCATE TABLE analytics.facts_reviews RESTART IDENTITY;
    INSERT INTO analytics.facts_reviews
        (review_id, order_id, product_key, review_score,
         review_comment_message, review_creation_date, linked_to_product)
    SELECT r.review_id, r.order_id, dp.product_key, r.review_score,
           r.review_comment_message, r.review_creation_date,
           dp.product_key IS NOT NULL
    FROM staging.reviews r
    LEFT JOIN LATERAL (
        SELECT product_id FROM staging.order_items oi
        WHERE oi.order_id = r.order_id
        ORDER BY order_item_id LIMIT 1
    ) oi ON TRUE
    LEFT JOIN analytics.dim_products dp USING (product_id);
    """
    hook = _hook()
    hook.run(sql)
    return hook.get_first("SELECT COUNT(*) FROM analytics.facts_reviews")[0]


def count_orphan_facts() -> int:
    return _hook().get_first(
        """
        SELECT COUNT(*) FROM analytics.facts_sales fs
        WHERE NOT EXISTS (
            SELECT 1 FROM analytics.dim_products dp
            WHERE dp.product_key = fs.product_key
        )
        """
    )[0]
