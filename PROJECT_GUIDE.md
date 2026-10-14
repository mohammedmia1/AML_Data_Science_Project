# Project walkthrough | AML investigation prioritization

This document provides the **human-readable journey** behind the published case study. Start with the [README](README.md), then use this page when you want the technical explanation or interview-ready reasoning.

## 1. Define the decision before building the model

A risk score is not useful by itself if investigators can review only a small set of records. The operational abstraction is a **ranked list of account-days** and a **fixed number of review slots**. The evaluation question is: *How many synthetic positives appear in that fixed queue?*

The benchmark target is `has_laundering_tx`, a synthetic label. It is neither a legal conclusion nor an observed investigator outcome.

## 2. Define the analytical grain and feature contract

The modeling table contains one row for each `account_id` and `activity_date`. The SQL source demonstrates how synthetic payments can be expanded into account-centric outgoing and incoming activities before aggregating counts, amounts, unique banks, currency diversity, and rapid transactions. The model uses nine engineered predictors: `log_transaction_count`, `log_total_sent`, `log_total_received`, `log_avg_transaction_amount`, `log_max_transaction_amount`, `log_unique_banks`, `outgoing_ratio`, `currency_diversity`, and `rapid_transaction_ratio`.

The frozen modeling TSV is identified by SHA-256 in [data/README.md](data/README.md). The SQL script in [sql/](sql/AML_Portfolio_Pipeline.sql) is a source-reconstruction demonstration, not independently verified raw-to-model lineage.

## 3. Reduce temporal leakage

A random row-level split could put the same account's later behavior into training while testing on an earlier date. Therefore the project uses a chronological split:

| Partition | Dates, 2022 | Account-day rows | Role |
|:---|:---|---:|:---|
| Training | Sep 1–6 | 1,534,403 | Fit model and training-only class weight |
| Validation | Sep 7–8 | 450,244 | Choose evaluation policy and compare candidate methods |
| Test | Sep 9–10 | 494,707 | Report held-out results once |

Account IDs and timestamps are excluded from predictors. This reduces obvious look-ahead, but does not prove that the synthetic benchmark's label-generating process generalizes to operational AML cases.

## 4. Compare methods and freeze the challenger

The [notebook](notebooks/AML_Model_Development.ipynb) includes a standardized, class-balanced logistic-regression baseline and an XGBoost challenger. The published serialized model is XGBoost with 300 trees, max depth 5, learning rate 0.05, subsampling 0.8, column subsampling 0.8, seed 42 and two threads. The code uses nine features and training-derived class weights.

**Important:** The current published artifacts preserve final-model test metrics, but do not publish a numeric side-by-side baseline comparison. Do not claim an exact improvement over logistic regression without producing and validating that comparison on the validation partition.

## 5. Convert ranking into a review decision

A validation review budget of 2,500 account-days corresponds to 2,747 slots at the same review fraction in the held-out test period. Sort test records by predicted score in descending order, with stable tie handling, and select the first 2,747.

The held-out set has 1,499 positive synthetic labels. Of the 2,747 selected records, 389 have positive labels:

- **Precision at capacity:** 389 / 2,747 = **14.16%**.
- **Recall at capacity:** 389 / 1,499 = **25.95%**.
- **Lift:** selected precision divided by the held-out positive-label prevalence = **46.73×**.

ROC-AUC is 0.8523 and average precision (PR-AUC) is 0.1214. These are ranking metrics across thresholds, rather than measured operational returns.

## 6. Communicate the trade-off

The [GitHub Pages case study](https://mohammedmia1.github.io/AML_Data_Science_Project/) reads 15,000 capacity points derived from the held-out score ranking. Moving the slider changes how many account-days are hypothetically reviewed and shows resulting precision, recall and positive-label capture. The default marker corresponds to the **frozen 2,747-slot policy**.

The optional [Tableau workbook](tableau/AML_Investigation_Prioritization_Dashboard.twbx) is a downloadable dashboard companion. GitHub displays a file/download page, not a Tableau preview; open the `.twbx` in Tableau Public to interact with its native workbook.

## 7. Reproduce what was actually validated

Install the pinned requirements, provide the exact source TSV, then run:

```bash
python src/run_canonical.py
python tests/check_artifacts.py
```

The script checks the source SHA-256 before fitting and writes the model, scored data, metrics and capacity curve. The published results were independently re-created from the frozen source during portfolio QA. A standard GitHub Actions run **does not retrain** because the TSV is too large to include in the repository.

### Verification boundaries

| Component | Verified scope | What is **not** established |
|:---|:---|:---|
| Canonical training | Full independent rerun of frozen TSV and byte-for-byte artifact reconciliation during QA | Real-world validation |
| Website | Published capacity curve and fixed metrics cross-checked against canonical scored test rows; site reported accessible | Production uptime or business impact |
| CI | Published artifact contract, code compilation, notebook structure | Full retraining or complete notebook execution |
| SQL | Structure and expected modeling columns reviewed | Fresh raw-transactions-to-TSV exact reconciliation |
| Tableau | Working workbook available as a companion | Fully finished visual polish or automated Tableau rendering in CI |

## 8. Answers to likely reviewer questions

**Why account-day instead of transaction-level?** It provides a consistent time-window representation of aggregate behavior and turns scarce investigative attention into a rankable unit. It also means the same account may appear on multiple days.

**Why chronological splitting?** The hypothetical investigator scores future activity using historical observations. A time-based split better represents that setting than shuffling rows.

**Why PR-AUC and precision at capacity?** Positive labels are rare, and review capacity is constrained. Overall accuracy is not an informative primary metric for this application.

**Why is 46.73× lift not a 46.73× business improvement?** It is a mathematical concentration ratio against random sampling at a fixed budget. No labor savings, dollar losses, or investigator outcomes were measured.

**Is the SQL pipeline end-to-end reproducible?** The source-to-feature logic is documented, but the exact frozen source was not regenerated from the raw transactions during this release. The modeling run *from the frozen TSV* is reproducible.

**Why not serve the full original dataset?** The 237.7 MB modeling TSV is not checked into the repo. The checksum and schema establish the exact required input without presenting a similarly named benchmark extract as equivalent.

## Next iteration, without rewriting validated history

1. Independently reconcile raw MySQL export with the exact TSV used for training.
2. Add numeric logistic-vs-XGBoost validation comparisons and stronger temporal holdouts if source data permits.
3. Consider a compact precomputed analytical export for browser-accessible SQL results and deeper explanations.
4. Refine Tableau layout independently from the frozen metrics and GitHub Pages interface.
