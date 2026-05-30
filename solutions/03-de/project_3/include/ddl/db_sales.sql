DROP TABLE IF EXISTS order_items CASCADE;
DROP TABLE IF EXISTS orders CASCADE;

CREATE TABLE orders (
    order_id                      VARCHAR(32) PRIMARY KEY,
    customer_id                   VARCHAR(32) NOT NULL,
    order_status                  VARCHAR(32),
    order_purchase_timestamp      TIMESTAMP,
    order_approved_at             TIMESTAMP,
    order_delivered_carrier_date  TIMESTAMP,
    order_delivered_customer_date TIMESTAMP,
    order_estimated_delivery_date TIMESTAMP
);

CREATE TABLE order_items (
    order_id            VARCHAR(32),
    order_item_id       SMALLINT,
    product_id          VARCHAR(32) NOT NULL,
    seller_id           VARCHAR(32),
    shipping_limit_date TIMESTAMP,
    price               NUMERIC(10, 2) CHECK (price >= 0),
    freight_value       NUMERIC(10, 2) CHECK (freight_value >= 0),
    PRIMARY KEY (order_id, order_item_id)
);
