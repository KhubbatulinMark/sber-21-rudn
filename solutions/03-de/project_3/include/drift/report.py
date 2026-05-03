import json
from datetime import datetime
from pathlib import Path

import pandas as pd
from evidently import ColumnMapping
from evidently.metric_preset import DataDriftPreset, DataQualityPreset
from evidently.report import Report

from include.drift.sql import CATEGORICAL_FEATURES, NUMERICAL_FEATURES, TARGET


def _column_mapping() -> ColumnMapping:
    return ColumnMapping(
        target=TARGET,
        numerical_features=NUMERICAL_FEATURES,
        categorical_features=CATEGORICAL_FEATURES,
    )


def build_drift_report(
    reference_path: Path, current_path: Path, output_dir: Path
) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    reference = pd.read_parquet(reference_path)
    current = pd.read_parquet(current_path)

    keep = [c for c in NUMERICAL_FEATURES + CATEGORICAL_FEATURES + [TARGET]
            if c in reference.columns and c in current.columns]
    reference = reference[keep].loc[:, reference[keep].nunique() > 1]
    current = current[reference.columns]

    report = Report(metrics=[DataDriftPreset(), DataQualityPreset()])
    report.run(reference_data=reference, current_data=current,
               column_mapping=_column_mapping())

    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%S")
    html_path = output_dir / f"report_{ts}.html"
    json_path = output_dir / f"report_{ts}.json"
    report.save_html(str(html_path))
    json_path.write_text(json.dumps(report.as_dict(), default=str))
    return html_path, json_path


def parse_drift_summary(json_path: Path) -> dict:
    payload = json.loads(json_path.read_text())
    drift_metric = next(
        m for m in payload["metrics"] if m["metric"] == "DatasetDriftMetric"
    )
    result = drift_metric["result"]
    return {
        "share_of_drifted_columns": float(result["share_of_drifted_columns"]),
        "dataset_drift": bool(result["dataset_drift"]),
        "n_drifted_features": int(result["number_of_drifted_columns"]),
        "n_features": int(result["number_of_columns"]),
    }
