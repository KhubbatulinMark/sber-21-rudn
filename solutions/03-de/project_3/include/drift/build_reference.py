"""
Standalone script: build the reference dataset for drift monitoring.

Usage (run from the Airflow worker or locally against the warehouse):
    python include/drift/build_reference.py

Saves artefacts/drift/reference.parquet.
"""
from pathlib import Path

import pandas as pd
from airflow.providers.postgres.hooks.postgres import PostgresHook

from include.drift.sql import CATEGORICAL_FEATURES, FEATURES_SQL, NUMERICAL_FEATURES, TARGET

REFERENCE_PATH = Path("/opt/airflow/artefacts/drift/reference.parquet")


def build_reference(output_path: Path = REFERENCE_PATH) -> Path:
    """Query the warehouse and persist a reference sample for Evidently.

    The reference is built from the full historical dataset available in
    analytics.facts_sales / facts_reviews / dim_products.  Features are
    restricted to those used by the ML model so the ColumnMapping stays
    consistent between training and monitoring.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    conn = PostgresHook(postgres_conn_id="postgres_warehouse").get_conn()
    try:
        df = pd.read_sql(FEATURES_SQL, conn)
    finally:
        conn.close()

    keep = NUMERICAL_FEATURES + CATEGORICAL_FEATURES + [TARGET]
    reference = df[[c for c in keep if c in df.columns]].dropna(subset=[TARGET])
    reference.to_parquet(output_path, index=False)
    print(f"Reference saved to {output_path} ({len(reference)} rows)")
    return output_path


if __name__ == "__main__":
    build_reference()
