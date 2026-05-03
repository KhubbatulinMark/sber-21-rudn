"""Shared SQL: feature dataset for training, inference and drift monitoring."""

FEATURES_SQL = """
SELECT
    fs.order_id,
    fs.order_item_id,
    fs.order_purchase_timestamp,
    fs.price,
    fs.freight_value,
    fs.revenue,
    dp.product_category_name_english,
    fr.review_score
FROM analytics.facts_sales fs
JOIN analytics.dim_products dp ON dp.product_key = fs.product_key
LEFT JOIN analytics.facts_reviews fr ON fr.order_id = fs.order_id
WHERE fr.review_score IS NOT NULL
"""

NUMERICAL_FEATURES = ["price", "freight_value", "revenue"]
CATEGORICAL_FEATURES = ["product_category_name_english"]
TARGET = "review_score"
