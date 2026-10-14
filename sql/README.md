# SQL account-day engineering

`AML_Portfolio_Pipeline.sql` documents a runnable MySQL 8+ transformation from synthetic raw transactions into development and later-period account-day views. It preserves the account-centric sender/receiver expansion, ten-minute rapid activity flag, daily aggregations, and frozen model-input columns used by the project.

**Verification scope:** The pipeline's logic was reconstructed from the original project SQL and reviewed structurally, but **not reexecuted against the original raw transaction CSV** in this environment. The canonical model is independently reproducible from the exact frozen development TSV listed in `data/README.md`. Do not claim that a fresh raw-SQL rebuild has passed bit-for-bit reconciliation unless you actually rerun it and compare exports.

Prerequisite: create `aml_portfolio.raw_transactions` with the required field names/types and load the synthetic AML benchmark transactions. Execute the SQL in MySQL 8+, export `vw_modeling_dev` with matching column order and precision, then compare split counts, labels, and source hash to the frozen TSV before rerunning the Python pipeline.
