CREATE TABLE IF NOT EXISTS analytics.predictions (
    prediction_id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    order_id               VARCHAR(32) NOT NULL,
    prediction_ts          TIMESTAMP   NOT NULL DEFAULT NOW(),
    model_name             VARCHAR(64) NOT NULL,
    predicted_review_score NUMERIC(3, 2) NOT NULL CHECK (predicted_review_score BETWEEN 1 AND 5)
);
