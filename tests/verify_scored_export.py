"""Audit canonical 17-column scored export for Tableau and ranked-queue logic.

Usage: python tests/verify_scored_export.py path/to/scored.csv
This check consumes the *entire* scored CSV and requires pandas from requirements.txt.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_COLUMNS = [
    "account_id", "activity_date", "transaction_count", "outgoing_ratio",
    "total_sent", "total_received", "avg_transaction_amount",
    "max_transaction_amount", "unique_counterparties", "unique_banks",
    "currency_diversity", "rapid_transaction_ratio", "has_laundering_tx",
    "risk_score", "risk_rank", "selected_for_review", "model_outcome",
]


def verify(path: Path) -> dict:
    metrics = json.loads((ROOT / "reports/metrics.json").read_text())
    frame = pd.read_csv(path, dtype={"account_id": str})
    if list(frame.columns) != EXPECTED_COLUMNS:
        raise AssertionError("Unexpected scored-export columns or column order")
    if len(frame) != metrics["test_rows"]:
        raise AssertionError("Scored-export row count differs from published metrics")
    if frame[["account_id", "activity_date"]].duplicated().any():
        raise AssertionError("Duplicate account-day key")
    ranks = frame["risk_rank"]
    if ranks.isna().any() or not ranks.is_unique or ranks.min() != 1 or ranks.max() != len(frame):
        raise AssertionError("Risk ranks must be a complete unique sequence from 1 to N")
    if not frame["risk_score"].notna().all():
        raise AssertionError("Missing risk scores")
    if not frame["has_laundering_tx"].isin([0, 1]).all():
        raise AssertionError("Invalid binary target")
    if not frame["selected_for_review"].isin([0, 1]).all():
        raise AssertionError("Invalid selection indicator")

    positives = frame["has_laundering_tx"].eq(1)
    selected = frame["selected_for_review"].eq(1)
    if not (selected == ranks.le(metrics["test_capacity"])).all():
        raise AssertionError("Selection does not agree with capacity and risk rank")
    expected_outcome = pd.Series("True Negative", index=frame.index)
    expected_outcome.loc[~selected & positives] = "False Negative"
    expected_outcome.loc[selected & ~positives] = "False Positive"
    expected_outcome.loc[selected & positives] = "True Positive"
    if not (frame["model_outcome"] == expected_outcome).all():
        raise AssertionError("Review outcome labels do not agree with selection and target")

    positive_count = int(positives.sum())
    review_count = int(selected.sum())
    selected_positive_count = int((selected & positives).sum())
    expected_counts = (
        metrics["test_positives"], metrics["test_capacity"], metrics["selected_positives"]
    )
    if (positive_count, review_count, selected_positive_count) != expected_counts:
        raise AssertionError("Queue totals differ from published canonical results")
    if not math.isclose(selected_positive_count / review_count, metrics["precision"], rel_tol=1e-12):
        raise AssertionError("Precision differs from published metrics")
    if not math.isclose(selected_positive_count / positive_count, metrics["recall"], rel_tol=1e-12):
        raise AssertionError("Recall differs from published metrics")
    if not math.isclose(metrics["lift"], metrics["precision"] / (positive_count / len(frame)), rel_tol=1e-12):
        raise AssertionError("Lift differs from published metrics")
    return {
        "rows": len(frame),
        "selected": review_count,
        "positive_labels": positive_count,
        "selected_positive_labels": selected_positive_count,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv_path", type=Path)
    args = parser.parse_args()
    result = verify(args.csv_path)
    print("PASS: scored export", json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
