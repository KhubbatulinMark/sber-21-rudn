from pathlib import Path

import pandas as pd
from evidently.test_suite import TestSuite
from evidently.tests import TestColumnDrift, TestShareOfDriftedColumns

from include.drift.report import _column_mapping
from include.drift.sql import CATEGORICAL_FEATURES, NUMERICAL_FEATURES, TARGET


def _build_suite() -> TestSuite:
    return TestSuite(tests=[
        TestShareOfDriftedColumns(lt=0.3),
        TestColumnDrift(column_name="price", stattest_threshold=0.1),
        TestColumnDrift(column_name="freight_value", stattest_threshold=0.1),
        TestColumnDrift(column_name="product_category_name_english", stattest_threshold=0.1),
    ])


def run_test_suite(reference_path: Path, current_path: Path) -> dict:
    reference = pd.read_parquet(reference_path)
    current = pd.read_parquet(current_path)
    keep = [c for c in NUMERICAL_FEATURES + CATEGORICAL_FEATURES + [TARGET]
            if c in reference.columns and c in current.columns]
    reference = reference[keep].loc[:, reference[keep].nunique() > 1]
    current = current[reference.columns]

    suite = _build_suite()
    suite.run(reference_data=reference, current_data=current,
              column_mapping=_column_mapping())
    payload = suite.as_dict()
    failed = [
        {"name": t["name"], "description": t["description"]}
        for t in payload["tests"] if t["status"] != "SUCCESS"
    ]
    return {"all_passed": len(failed) == 0, "failed": failed}
