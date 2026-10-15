# Raw transaction to frozen account-day reconciliation

## Scope and inputs

The uploaded `HI-Small_Trans.csv` (5,078,345 raw transactions including all dates) was compared with the frozen, checksum-verified `aml_modeling_dev.tsv` (2,479,354 account-day records; SHA-256 `d6194ac2c29f4a90e4fa1e1740945ca2f558388a799020a15f16623eee9c6012`). Both are **synthetic**, not customer records.

This comparison reconstructed the published MySQL account-centric transformation in **Python/pandas**, including outgoing and incoming transaction perspectives, daily aggregation, unique counterparties, bank/currency diversity, rapid-transaction ratio (time difference <= 10 minutes), and account-day labels. The original MySQL script was **not executed in MySQL**. Do not represent the checks as a successful MySQL rerun or byte-identical TSV reproduction.

## Findings, September 1-10, 2022

| Comparison | Finding |
|---|---:|
| Raw transactions in modeling window | 5,077,237 |
| Account-perspective activity records | 10,154,474 |
| Account-day keys in reconstructed and frozen tables | 2,479,354 |
| Missing or extra `(account_id, activity_date)` keys | **0** |
| Transaction-count differences | **0** |
| Synthetic label differences | **0** |
| Positive account-day labels | **7,131** in both |
| Unique counterparties and currency diversity | Matching in checked per-day calculations |
| Outgoing and rapid-transaction ratios | Differences at or below 0.00005, consistent with frozen four-decimal rounding |
| Monetary aggregations | Small floating-point differences, maximum seen 0.0001220703125 on the checked per-day calculations |
| Unique-bank counts using raw bank codes as strings | Some one-bank differences |
| Unique-bank counts after normalizing numeric bank IDs | **0 mismatches across all 10 days** |

All the raw bank identifiers checked contained decimal digits. The raw CSV can represent one bank as `010` and `0010`; string-based DISTINCT treats them as different, while treating bank codes as numeric collapses the duplicates. For example, account `8034780B0` on September 10 differs by one unique bank before normalization but not after. Thus the SQL implementation should normalize `from_bank` and `to_bank` before calculating distinct counterparty banks. This patch uses `CAST(... AS UNSIGNED)` for this *numeric-coded* benchmark.

## Interpretation and boundaries

This establishes strong raw-to-model **logical lineage** for the tested account-day fields and explains the observed bank-ID discrepancy. It does **not** establish an identical TSV file hash or an independently executed MySQL export. Differences in row order, floating-point precision, rounding, database type choices, and export formatting can change the bytes without changing equivalent values. Formal closure of MySQL reproducibility would require loading the original CSV with a documented schema, running the modified SQL in MySQL 8+, exporting all 13 columns and comparing keyed feature values under documented tolerances.

The existing model's frozen inputs, trained XGBoost artifact, held-out ranking metrics, and website were not modified during this reconciliation.
