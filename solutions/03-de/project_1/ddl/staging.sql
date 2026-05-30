CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS analytics;

CREATE TABLE IF NOT EXISTS staging.orders (
    order_id                      TEXT PRIMARY KEY,
    customer_id                   TEXT NOT NULL,
    order_status                  TEXT NOT NULL,
    order_purchase_timestamp      TIMESTAMP NOT NULL,
    order_approved_at             TIMESTAMP,
    order_delivered_carrier_date  TIMESTAMP,
    order_delivered_customer_date TIMESTAMP,
    order_estimated_delivery_date TIMESTAMP
);

CREATE TABLE IF NOT EXISTS staging.order_items (
    order_id            TEXT NOT NULL,
    order_item_id       SMALLINT NOT NULL,
    product_id          TEXT NOT NULL,
    seller_id           TEXT NOT NULL,
    shipping_limit_date TIMESTAMP,
    price               NUMERIC(10, 2) NOT NULL,
    freight_value       NUMERIC(10, 2) NOT NULL,
    PRIMARY KEY (order_id, order_item_id)
);

CREATE TABLE IF NOT EXISTS staging.products (
    product_id                 TEXT PRIMARY KEY,
    product_category_name      TEXT,
    product_name_lenght        SMALLINT,
    product_description_lenght SMALLINT,
    product_photos_qty         SMALLINT,
    product_weight_g           INTEGER,
    product_length_cm          SMALLINT,
    product_height_cm          SMALLINT,
    product_width_cm           SMALLINT
);

CREATE TABLE IF NOT EXISTS staging.category_translation (
    product_category_name         TEXT PRIMARY KEY,
    product_category_name_english TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS staging.reviews (
    review_key              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    review_id               TEXT NOT NULL,
    order_id                TEXT NOT NULL,
    review_score            SMALLINT NOT NULL CHECK (review_score BETWEEN 1 AND 5),
    review_comment_title    TEXT,
    review_comment_message  TEXT,
    review_creation_date    TIMESTAMP NOT NULL,
    review_answer_timestamp TIMESTAMP
);
