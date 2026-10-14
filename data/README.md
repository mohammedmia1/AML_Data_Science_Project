# Dataset and lineage

The input `aml_modeling_dev.tsv` is a transaction-derived, **synthetic** account-day table (not customer data). It is not included because it is 237.7 MB, above GitHub’s regular per-file limit. The source transaction dataset used during development was named `HI-Small_Trans.csv` and is associated with the IBM AMLSim benchmark ecosystem; obtain the appropriate licensed version and rebuild the account-day table with the project SQL pipeline. A similarly named dataset is **not automatically equivalent** to the precise modeling TSV used for these results.

To reproduce the **exact** published numbers, supply the identical development TSV. Its SHA-256 is:

`d6194ac2c29f4a90e4fa1e1740945ca2f558388a799020a15f16623eee9c6012`

Place the TSV at `data/local/aml_modeling_dev.tsv` or set `AML_INPUT_DIR` to its parent folder. The script verifies shape and records the input checksum. The source data is not redistributed in this repository.

Columns: `account_id`, `activity_date`, `transaction_count`, `outgoing_ratio`, `total_sent`, `total_received`, `avg_transaction_amount`, `max_transaction_amount`, `unique_counterparties`, `unique_banks`, `currency_diversity`, `rapid_transaction_ratio`, `has_laundering_tx`.

**Limitations:** Synthetic labels indicate benchmark events, not verified real-world crimes.
