# SQL account-day engineering

`AML_Portfolio_Pipeline.sql` documents a runnable MySQL 8+ transformation from synthetic raw transactions into development and later-period account-day views. It preserves the account-centric sender/receiver expansion, ten-minute rapid activity flag, daily aggregations, and frozen model-input columns used by the project.

**Verification scope:** The supplied raw synthetic CSV has been compared to the frozen model table using an independent Python/pandas reconstruction of the SQL logic. All 2,479,354 account-day keys, counts and labels agree. Bank codes with different zero padding are now normalized in the SQL (`CAST(... AS UNSIGNED)`) to match the frozen unique-bank results. See [the reconciliation report](../reports/SQL_RECONCILIATION.md) for feature checks and remaining limitations. **The MySQL script has not been run end-to-end against the raw CSV, and the raw-to-TSV export has not been proven byte-identical.**

Prerequisite: create `aml_portfolio.raw_transactions` with the required field names/types and load the synthetic AML benchmark transactions. Execute the SQL in MySQL 8+, export `vw_modeling_dev` with matching column order and precision, then compare keyed counts, labels, and feature values against the frozen TSV using documented tolerances before rerunning the Python pipeline.
