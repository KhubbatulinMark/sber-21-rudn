DROP TABLE IF EXISTS reviews CASCADE;
DROP TABLE IF EXISTS category_translation CASCADE;
DROP TABLE IF EXISTS products CASCADE;

CREATE TABLE products (
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

CREATE TABLE category_translation (
    product_category_name         VARCHAR(64) PRIMARY KEY,
    product_category_name_english VARCHAR(64)
);

CREATE TABLE reviews (
    review_key              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    review_id               VARCHAR(32),
    order_id                VARCHAR(32),
    review_score            SMALLINT CHECK (review_score BETWEEN 1 AND 5),
    review_comment_title    TEXT,
    review_comment_message  TEXT,
    review_creation_date    TIMESTAMP,
    review_answer_timestamp TIMESTAMP
);
