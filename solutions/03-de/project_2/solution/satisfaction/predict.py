"""CLI inference script: load model + transformer and produce predictions."""
import argparse
import pickle

import pandas as pd

from satisfaction.data import read_data
from satisfaction.data.make_dataset import drop_unused_columns
from satisfaction.features import engineer_features, make_features
from satisfaction.models import predict_model


DEFAULT_DROP = [
    "customer_id",
    "product_id",
    "review_id",
    "customer_city",
    "customer_zip_code_prefix",
    "review_comment_title",
    "review_comment_message",
    "review_creation_date",
    "review_answer_timestamp",
    "review_score",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Batch inference for Olist review score")
    parser.add_argument("--model-path", required=True)
    parser.add_argument("--transformer-path", required=True)
    parser.add_argument("--input-path", required=True)
    parser.add_argument("--output-path", required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    with open(args.model_path, "rb") as f:
        model = pickle.load(f)
    with open(args.transformer_path, "rb") as f:
        transformer = pickle.load(f)

    raw = read_data(args.input_path)
    order_ids = raw["order_id"].copy()
    data = drop_unused_columns(raw, DEFAULT_DROP)
    data = engineer_features(data)
    features = make_features(transformer, data)

    predictions = predict_model(model, features)

    out = pd.DataFrame(
        {"order_id": order_ids, "predicted_review_score": predictions}
    )
    out.to_csv(args.output_path, index=False)
    print(f"Saved {len(out)} predictions to {args.output_path}")


if __name__ == "__main__":
    main()
