# Model evaluation

## Holdout design

Training: 2022-09-01 through 2022-09-06 (1,534,403 account-days). Validation: 2022-09-07 through 2022-09-08 (450,244). Test: 2022-09-09 through 2022-09-10 (494,707). Split chronologically to avoid future information entering training.

## Frozen policy and results

The model uses nine engineered predictors. A validation policy of 2,500 reviews corresponds to 2,747 test reviews at the same fraction. Held-out test labels include 1,499 positives, of which 389 were selected. Precision 14.1609%; recall 25.9506%; lift 46.7345x; ROC-AUC 0.85225494; average precision (PR-AUC) 0.12141259. These numbers are calculated from the canonical run and checked against `reports/metrics.json`.

## Validation comparison (model selection evidence)

With the **same 2,500-account-day validation review budget**, a logistic-regression baseline had PR-AUC **0.0378**, ROC-AUC **0.7995**, and **170** positive synthetic labels among reviewed rows (**6.80% precision**). XGBoost had PR-AUC **0.1286**, ROC-AUC **0.8446**, and **383** positive labels (**15.32% precision**). These are the recorded outputs of the [executed notebook](../notebooks/AML_Model_Development.ipynb); they are not held-out test results and should not be interpreted as real-world effectiveness.

## Model specification

XGBoost: 300 trees, depth 5, learning rate 0.05, subsample 0.8, column subsample 0.8, positive class weight derived from training labels, random state 42. Numeric counts/amounts and `unique_banks` are transformed with `log1p`. The published pipeline trains on the training partition only; validation selects the operating review rate.

## Limitations

Synthetic labels, severe class imbalance, possible population shift, unknown real investigation costs, and uncalibrated risk scores limit external validity. The held-out test period is short. This project is not a deployed monitoring system or proof of crime.

## Reproduction

Use Python 3.13.5 and pinned `requirements.txt`, provide the exact development TSV (SHA-256 in `data/README.md`), then run `python src/run_canonical.py`. The script emits `artifacts/metrics.json`, `artifacts/capacity.json`, `artifacts/xgboost_canonical.json`, and `artifacts/aml_tableau_decision_data_canonical.csv`. Compare results against the committed metrics and chart data.
