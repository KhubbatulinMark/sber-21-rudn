CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS analytics;

CREATE TABLE IF NOT EXISTS staging.orders (
    order_id                      VARCHAR(32) PRIMARY KEY,
    customer_id                   VARCHAR(32) NOT NULL,
    order_status                  VARCHAR(32),
    order_purchase_timestamp      TIMESTAMP,
    order_approved_at             TIMESTAMP,
    order_delivered_carrier_date  TIMESTAMP,
    order_delivered_customer_date TIMESTAMP,
    order_estimated_delivery_date TIMESTAMP
);

CREATE TABLE IF NOT EXISTS staging.order_items (
    order_id            VARCHAR(32),
    order_item_id       SMALLINT,
    product_id          VARCHAR(32) NOT NULL,
    seller_id           VARCHAR(32),
    shipping_limit_date TIMESTAMP,
    price               NUMERIC(10, 2),
    freight_value       NUMERIC(10, 2),
    PRIMARY KEY (order_id, order_item_id)
);

CREATE TABLE IF NOT EXISTS staging.products (
    product_id                 VARCHAR(32) PRIMARY KEY,
    product_category_name      VARCHAR(64),
    product_name_lenght        SMALLINT,
    product_description_lenght SMALLINT,
    product_photos_qty         SMALLINT,
    product_weight_g           INTEGER,
    product_length_cm          SMALLINT,
    product_height_cm          SMALLINT,
    product_width_cm           SMALLINT
);

CREATE TABLE IF NOT EXISTS staging.category_translation (
    product_category_name         VARCHAR(64) PRIMARY KEY,
    product_category_name_english VARCHAR(64)
);

CREATE TABLE IF NOT EXISTS staging.reviews (
    review_key              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    review_id               VARCHAR(32),
    order_id                VARCHAR(32),
    review_score            SMALLINT,
    review_comment_title    TEXT,
    review_comment_message  TEXT,
    review_creation_date    TIMESTAMP,
    review_answer_timestamp TIMESTAMP
);

CREATE TABLE IF NOT EXISTS analytics.dim_products (
    product_key                   BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    product_id                    VARCHAR(32) UNIQUE NOT NULL,
    product_category_name         VARCHAR(64),
    product_category_name_english VARCHAR(64)
);

CREATE TABLE IF NOT EXISTS analytics.facts_sales (
    fact_id                  BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    order_id                 VARCHAR(32) NOT NULL,
    order_item_id            SMALLINT NOT NULL,
    product_key              BIGINT NOT NULL REFERENCES analytics.dim_products(product_key),
    order_purchase_timestamp TIMESTAMP,
    price                    NUMERIC(10, 2),
    freight_value            NUMERIC(10, 2),
    revenue                  NUMERIC(12, 2)
);

CREATE TABLE IF NOT EXISTS analytics.facts_reviews (
    fact_id                BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    review_id              VARCHAR(32),
    order_id               VARCHAR(32),
    product_key            BIGINT REFERENCES analytics.dim_products(product_key),
    review_score           SMALLINT,
    review_comment_message TEXT,
    review_creation_date   TIMESTAMP,
    linked_to_product      BOOLEAN NOT NULL
);
