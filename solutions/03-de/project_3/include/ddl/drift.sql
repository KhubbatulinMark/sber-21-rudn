CREATE TABLE IF NOT EXISTS analytics.drift_metrics (
    metric_id                BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    run_ts                   TIMESTAMP NOT NULL,
    window_start             DATE NOT NULL,
    window_end               DATE NOT NULL,
    share_of_drifted_columns NUMERIC(5, 4) NOT NULL,
    dataset_drift            BOOLEAN NOT NULL,
    n_drifted_features       INTEGER NOT NULL,
    n_features               INTEGER NOT NULL,
    report_path              TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS analytics.drift_incidents (
    incident_id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    run_ts               TIMESTAMP NOT NULL,
    failed_tests         JSONB NOT NULL,
    report_path          TEXT NOT NULL,
    triggered_dag_run_id TEXT
);
