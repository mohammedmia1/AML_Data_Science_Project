"""Reproduce the frozen synthetic-AML XGBoost investigation ranking.

Input: exact SHA-256-verified account-day TSV under AML_INPUT_DIR (default data/local).
Output: model, scored CSV, metrics, and 15,000-point website curve under AML_OUTPUT_DIR.

The parameters, row ordering, and serialized artifacts intentionally preserve the
published canonical run. This is *not* a raw-transactions-to-TSV reconstruction.
"""

from __future__ import annotations

import hashlib
import json
import os
import platform
from pathlib import Path

import numpy as np
import pandas as pd
import sklearn
import xgboost
from sklearn.metrics import average_precision_score, roc_auc_score
from xgboost import XGBClassifier

SOURCE_NAME = "aml_modeling_dev.tsv"
SOURCE_SHA256 = "d6194ac2c29f4a90e4fa1e1740945ca2f558388a799020a15f16623eee9c6012"
EXPECTED_SPLIT_ROWS = (1_534_403, 450_244, 494_707)
VALIDATION_CAPACITY = 2_500
PUBLISHED_TEST_CAPACITY = 2_747
MAX_CURVE_CAPACITY = 15_000
SEED = 42
THREADS = 2

LOG_FEATURES = [
    "transaction_count", "total_sent", "total_received",
    "avg_transaction_amount", "max_transaction_amount", "unique_banks",
]
DIRECT_FEATURES = [
    "outgoing_ratio", "currency_diversity", "rapid_transaction_ratio",
]


def source_checksum(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def load_source(path: Path) -> tuple[pd.DataFrame, str]:
    sha256 = source_checksum(path)
    if sha256 != SOURCE_SHA256:
        raise ValueError("Input TSV differs from the validated canonical source")
    data = pd.read_csv(path, sep="\t")
    data["activity_date"] = pd.to_datetime(data.activity_date)
    if data[["account_id", "activity_date"]].duplicated().any():
        raise ValueError("Duplicate account-day keys in source TSV")
    return data, sha256


def split_by_date(data: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    train = data[data.activity_date.between("2022-09-01", "2022-09-06")]
    validation = data[data.activity_date.between("2022-09-07", "2022-09-08")]
    test = data[data.activity_date.between("2022-09-09", "2022-09-10")].copy()
    counts = (len(train), len(validation), len(test))
    if counts != EXPECTED_SPLIT_ROWS:
        raise ValueError(f"Unexpected temporal split sizes: {counts}")
    return train, validation, test


def make_features(data: pd.DataFrame) -> pd.DataFrame:
    """Preserve the exact feature names and column order of the canonical model."""
    features = pd.DataFrame(index=data.index)
    for column in LOG_FEATURES:
        features["log_" + column] = np.log1p(data[column])
    for column in DIRECT_FEATURES:
        features[column] = data[column]
    if not np.isfinite(features.to_numpy()).all():
        raise ValueError("Non-finite values in model features")
    return features


def make_model(train_labels: pd.Series) -> XGBClassifier:
    # Preserve the original Python float expression; model bytes are regression-tested.
    class_weight = int((train_labels == 0).sum()) / int((train_labels == 1).sum())
    return XGBClassifier(
        n_estimators=300,
        max_depth=5,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        objective="binary:logistic",
        eval_metric="aucpr",
        scale_pos_weight=class_weight,
        random_state=SEED,
        n_jobs=THREADS,
    )


def rank_test_records(test: pd.DataFrame, scores: np.ndarray, capacity: int) -> tuple[pd.DataFrame, np.ndarray]:
    """Rank descending with stable tie handling in original input-row order."""
    rank_order = np.argsort(-scores, kind="stable")
    ranks = np.empty(len(test), dtype=np.int32)
    ranks[rank_order] = np.arange(1, len(test) + 1)

    test["risk_score"] = scores
    test["risk_rank"] = ranks
    test["selected_for_review"] = (ranks <= capacity).astype("int8")
    selected = test.selected_for_review.eq(1)
    positive = test.has_laundering_tx.eq(1)
    test["model_outcome"] = np.select(
        [selected & positive, selected & ~positive, ~selected & positive],
        ["True Positive", "False Positive", "False Negative"],
        default="True Negative",
    )
    return test, rank_order


def make_metrics(
    train: pd.DataFrame,
    validation: pd.DataFrame,
    test: pd.DataFrame,
    scores: np.ndarray,
    features: pd.DataFrame,
    capacity: int,
    source_sha256: str,
) -> dict:
    target = test.has_laundering_tx
    positives = int(target.sum())
    selected_positives = int(test.loc[test.selected_for_review.eq(1), "has_laundering_tx"].sum())
    prevalence = float(target.mean())
    # Keep insertion order for byte-for-byte parity with the published JSON.
    return {
        "train_rows": len(train),
        "validation_rows": len(validation),
        "test_rows": len(test),
        "train_positives": int(train.has_laundering_tx.sum()),
        "validation_positives": int(validation.has_laundering_tx.sum()),
        "test_positives": positives,
        "validation_capacity": VALIDATION_CAPACITY,
        "test_capacity": capacity,
        "selected_positives": selected_positives,
        "precision": selected_positives / capacity,
        "recall": selected_positives / positives,
        "lift": (selected_positives / capacity) / prevalence,
        "roc_auc": roc_auc_score(target, scores),
        "pr_auc": average_precision_score(target, scores),
        "xgboost_version": xgboost.__version__,
        "pandas_version": pd.__version__,
        "sklearn_version": sklearn.__version__,
        "python_version": platform.python_version(),
        "seed": SEED,
        "n_jobs": THREADS,
        "features": features.columns.tolist(),
        "source_file_sha256": source_sha256,
    }


def make_capacity_curve(test: pd.DataFrame, order: np.ndarray) -> dict:
    labels = test.has_laundering_tx.to_numpy()[order].astype("int8")
    cumulative_positives = np.cumsum(labels, dtype=np.int64)
    total_positives = int(test.has_laundering_tx.sum())
    prevalence = float(test.has_laundering_tx.mean())
    rows = []
    for capacity in range(1, MAX_CURVE_CAPACITY + 1):
        positives = int(cumulative_positives[capacity - 1])
        precision = positives / capacity
        rows.append({
            "k": capacity,
            "tp": positives,
            "precision": precision,
            "recall": positives / total_positives,
            "lift": precision / prevalence,
        })
    return {
        "rows": rows,
        "provenance": "Canonical XGBoost 3.1.3 model; September 9-10 2022 test; frozen validation-derived review rate",
    }


def run(input_dir: Path, output_dir: Path) -> dict:
    data, source_sha256 = load_source(input_dir / SOURCE_NAME)
    train, validation, test = split_by_date(data)
    x_train = make_features(train)
    x_validation = make_features(validation)
    x_test = make_features(test)
    train_labels = train.has_laundering_tx
    model = make_model(train_labels)
    model.fit(x_train, train_labels)

    output_dir.mkdir(parents=True, exist_ok=True)
    model.save_model(output_dir / "xgboost_canonical.json")
    # Validation scores are computed to match the original frozen pipeline.
    _validation_scores = model.predict_proba(x_validation)[:, 1]
    test_scores = model.predict_proba(x_test)[:, 1]
    capacity = round(len(test) * VALIDATION_CAPACITY / len(validation))
    if capacity != PUBLISHED_TEST_CAPACITY:
        raise ValueError(f"Unexpected test review capacity: {capacity}")
    test, sorted_indices = rank_test_records(test, test_scores, capacity)
    test.to_csv(output_dir / "aml_tableau_decision_data_canonical.csv", index=False)

    metrics = make_metrics(train, validation, test, test_scores, x_train, capacity, source_sha256)
    (output_dir / "metrics.json").write_text(json.dumps(metrics, indent=2))
    curve = make_capacity_curve(test, sorted_indices)
    (output_dir / "capacity.json").write_text(json.dumps(curve, separators=(",", ":")))
    print(json.dumps(metrics, indent=2), flush=True)
    return metrics


if __name__ == "__main__":
    run(
        Path(os.environ.get("AML_INPUT_DIR", "data/local")),
        Path(os.environ.get("AML_OUTPUT_DIR", "artifacts")),
    )
