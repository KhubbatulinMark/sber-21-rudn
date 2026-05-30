CREATE TABLE IF NOT EXISTS analytics.dim_products (
    product_key                   BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    product_id                    TEXT UNIQUE NOT NULL,
    product_category_name         TEXT,
    product_category_name_english TEXT
);

CREATE TABLE IF NOT EXISTS analytics.facts_sales (
    sale_key                 BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    order_id                 TEXT NOT NULL,
    order_item_id            SMALLINT NOT NULL,
    product_key              BIGINT NOT NULL REFERENCES analytics.dim_products(product_key),
    order_purchase_timestamp TIMESTAMP NOT NULL,
    price                    NUMERIC(10, 2) NOT NULL,
    freight_value            NUMERIC(10, 2) NOT NULL,
    revenue                  NUMERIC(12, 2) GENERATED ALWAYS AS (price + freight_value) STORED,
    UNIQUE (order_id, order_item_id)
);

CREATE TABLE IF NOT EXISTS analytics.facts_reviews (
    review_key             BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    review_id              TEXT NOT NULL,
    order_id               TEXT NOT NULL,
    product_key            BIGINT REFERENCES analytics.dim_products(product_key),
    review_score           SMALLINT NOT NULL CHECK (review_score BETWEEN 1 AND 5),
    review_comment_message TEXT,
    review_creation_date   TIMESTAMP NOT NULL,
    linked_to_product      BOOLEAN NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_facts_sales_product_key
    ON analytics.facts_sales (product_key);
CREATE INDEX IF NOT EXISTS idx_facts_sales_purchase_ts
    ON analytics.facts_sales (order_purchase_timestamp);
CREATE INDEX IF NOT EXISTS idx_facts_reviews_product_key
    ON analytics.facts_reviews (product_key);
