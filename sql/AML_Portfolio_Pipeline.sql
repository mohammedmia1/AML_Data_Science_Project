/*
AML investigation prioritization — account-day feature engineering (MySQL 8+).
Input: aml_portfolio.raw_transactions, loaded from the synthetic AML benchmark.
This is a streamlined version of the feature logic used to produce the modeling
extracts. Numeric bank codes are normalized before DISTINCT counting. The account-day logic has been reconciled in pandas against the raw CSV
(see reports/SQL_RECONCILIATION.md), but the SQL has not been executed
in MySQL or shown to reproduce the exact TSV bytes.

Expected raw columns:
transaction_timestamp, from_bank, from_account, to_bank, to_account,
amount_received, receiving_currency, amount_paid, payment_currency,
payment_format, is_laundering.

Account-day labels are MAX(is_laundering) across both transaction perspectives;
they are synthetic benchmark labels, not adjudicated real-world cases.
*/
USE aml_portfolio;

-- One transaction from each account's perspective. UNION ALL is deliberate.
CREATE OR REPLACE VIEW vw_account_transactions AS
SELECT transaction_timestamp, DATE(transaction_timestamp) AS activity_date,
       from_account AS account_id, from_bank AS account_bank,
       to_account AS counterparty_account, CAST(to_bank AS UNSIGNED) AS counterparty_bank,
       'OUTGOING' AS direction, amount_paid AS amount,
       payment_currency AS currency, payment_format,
       CASE WHEN from_bank <> to_bank THEN 1 ELSE 0 END AS is_cross_bank,
       is_laundering
FROM raw_transactions
UNION ALL
SELECT transaction_timestamp, DATE(transaction_timestamp),
       to_account, to_bank, from_account, CAST(from_bank AS UNSIGNED),
       'INCOMING', amount_received, receiving_currency, payment_format,
       CASE WHEN from_bank <> to_bank THEN 1 ELSE 0 END,
       is_laundering
FROM raw_transactions;

DROP TABLE IF EXISTS account_daily_features_dev;
CREATE TABLE account_daily_features_dev AS
WITH ordered_activity AS (
  SELECT *, LAG(transaction_timestamp) OVER (
    PARTITION BY account_id, activity_date ORDER BY transaction_timestamp
  ) AS previous_transaction_timestamp
  FROM vw_account_transactions
  WHERE transaction_timestamp >= '2022-09-01 00:00:00'
    AND transaction_timestamp <  '2022-09-11 00:00:00'
)
SELECT account_id, activity_date,
       COUNT(*) AS transaction_count,
       SUM(CASE WHEN direction = 'OUTGOING' THEN 1 ELSE 0 END) AS outgoing_count,
       SUM(CASE WHEN direction = 'INCOMING' THEN 1 ELSE 0 END) AS incoming_count,
       SUM(CASE WHEN direction = 'OUTGOING' THEN amount ELSE 0 END) AS total_sent,
       SUM(CASE WHEN direction = 'INCOMING' THEN amount ELSE 0 END) AS total_received,
       AVG(amount) AS avg_transaction_amount,
       MAX(amount) AS max_transaction_amount,
       COUNT(DISTINCT counterparty_account) AS unique_counterparties,
       COUNT(DISTINCT counterparty_bank) AS unique_banks,
       COUNT(DISTINCT currency) AS currency_diversity,
       COUNT(DISTINCT payment_format) AS payment_format_diversity,
       SUM(CASE WHEN direction = 'OUTGOING' THEN amount ELSE 0 END) /
          NULLIF(SUM(CASE WHEN direction = 'INCOMING' THEN amount ELSE 0 END),0) AS sent_received_ratio,
       SUM(CASE WHEN previous_transaction_timestamp IS NOT NULL
                AND TIMESTAMPDIFF(MINUTE,previous_transaction_timestamp,transaction_timestamp) <= 10
           THEN 1 ELSE 0 END) AS rapid_transaction_count,
       AVG(is_cross_bank) AS cross_bank_ratio,
       MAX(is_laundering) AS has_laundering_tx
FROM ordered_activity
GROUP BY account_id, activity_date;

CREATE INDEX idx_dev_activity_date ON account_daily_features_dev(activity_date);
CREATE INDEX idx_dev_account_date ON account_daily_features_dev(account_id,activity_date);

CREATE OR REPLACE VIEW vw_modeling_dev AS
SELECT account_id, activity_date, transaction_count,
       outgoing_count / NULLIF(transaction_count,0) AS outgoing_ratio,
       total_sent, total_received, avg_transaction_amount,
       max_transaction_amount, unique_counterparties, unique_banks,
       currency_diversity,
       rapid_transaction_count / NULLIF(transaction_count,0) AS rapid_transaction_ratio,
       has_laundering_tx
FROM account_daily_features_dev;

DROP TABLE IF EXISTS account_daily_features_ood;
CREATE TABLE account_daily_features_ood AS
WITH ordered_activity AS (
  SELECT *, LAG(transaction_timestamp) OVER (
    PARTITION BY account_id,activity_date ORDER BY transaction_timestamp
  ) AS previous_transaction_timestamp
  FROM vw_account_transactions
  WHERE transaction_timestamp >= '2022-09-11 00:00:00'
)
SELECT account_id, activity_date,
       COUNT(*) AS transaction_count,
       SUM(CASE WHEN direction = 'OUTGOING' THEN 1 ELSE 0 END) AS outgoing_count,
       SUM(CASE WHEN direction = 'INCOMING' THEN 1 ELSE 0 END) AS incoming_count,
       SUM(CASE WHEN direction = 'OUTGOING' THEN amount ELSE 0 END) AS total_sent,
       SUM(CASE WHEN direction = 'INCOMING' THEN amount ELSE 0 END) AS total_received,
       AVG(amount) AS avg_transaction_amount,
       MAX(amount) AS max_transaction_amount,
       COUNT(DISTINCT counterparty_account) AS unique_counterparties,
       COUNT(DISTINCT counterparty_bank) AS unique_banks,
       COUNT(DISTINCT currency) AS currency_diversity,
       COUNT(DISTINCT payment_format) AS payment_format_diversity,
       SUM(CASE WHEN direction = 'OUTGOING' THEN amount ELSE 0 END) /
          NULLIF(SUM(CASE WHEN direction = 'INCOMING' THEN amount ELSE 0 END),0) AS sent_received_ratio,
       SUM(CASE WHEN previous_transaction_timestamp IS NOT NULL
                AND TIMESTAMPDIFF(MINUTE,previous_transaction_timestamp,transaction_timestamp) <= 10
           THEN 1 ELSE 0 END) AS rapid_transaction_count,
       AVG(is_cross_bank) AS cross_bank_ratio,
       MAX(is_laundering) AS has_laundering_tx
FROM ordered_activity
GROUP BY account_id,activity_date;

CREATE OR REPLACE VIEW vw_modeling_ood AS
SELECT account_id,activity_date,transaction_count,
       outgoing_count / NULLIF(transaction_count,0) AS outgoing_ratio,
       total_sent,total_received,avg_transaction_amount,
       max_transaction_amount,unique_counterparties,unique_banks,
       currency_diversity,
       rapid_transaction_count / NULLIF(transaction_count,0) AS rapid_transaction_ratio,
       has_laundering_tx
FROM account_daily_features_ood;

-- Reconciliation and quality checks (read-only).
SELECT CASE WHEN activity_date BETWEEN '2022-09-01' AND '2022-09-06' THEN 'train'
            WHEN activity_date BETWEEN '2022-09-07' AND '2022-09-08' THEN 'validation'
            WHEN activity_date BETWEEN '2022-09-09' AND '2022-09-10' THEN 'test'
       END AS split, COUNT(*) AS account_days, SUM(has_laundering_tx) AS positives
FROM vw_modeling_dev
GROUP BY split ORDER BY split;

SELECT COUNT(*) AS ood_rows,MIN(activity_date) AS min_date,
       MAX(activity_date) AS max_date,SUM(has_laundering_tx) AS positives
FROM vw_modeling_ood;

-- Export the 13 columns in vw_modeling_dev to a tab-separated UTF-8 file in
-- the same column order, then compare SHA-256 against data/README.md.
