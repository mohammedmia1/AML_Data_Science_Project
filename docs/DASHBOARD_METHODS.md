# Dashboard calculations

I use a frozen account-day ranking to explore review capacity, detection performance, and the USD transaction activity represented in the selected queue. The page loads precomputed aggregate values; it does not train a model in the browser.

## Ranking and cutoff

The canonical CSV contains 494,707 test account-days and 1,499 positive labels. At the original cutoff of 2,747, it captures 389 positives, with precision 14.16%, recall 25.95%, and F1 0.183. The dashboard uses the same canonical account-day ranking as the published model results.

For a prefix of k ranked account-days, I compute precision = TP / k, recall = TP / 1,499, and F1 = 2 × TP / (k + 1,499). Displayed precision is zero for an empty queue. Checking all 494,707 prefixes identifies a unique highest F1 at k = 822: 251 positives and F1 0.216286. This is a retrospective diagnostic, not a newly validated deployment cutoff. The interactive view covers the first 15,000 exact cutoffs, with a first-100 zoom.

## Transaction amounts

I fix the review snapshot at September 10, 2022, end of day, and include source activity from September 1–10. It is an account-history snapshot analysis, not a simulation of what was known at an earlier alert timestamp.

- **Review-linked volume:** unique eligible source transactions involving any account represented in the selected account-day prefix.
- **Positive-associated volume:** unique eligible source transactions involving an account with at least one positive account-day in the selected prefix. All eligible activity of those accounts is included, regardless of each transaction's individual label.

An eligible transaction has both payment and receiving currencies equal to US Dollar. I use amount paid, converted to integer cents before aggregation. No currency conversion is assumed. Both incoming and outgoing transactions qualify, but a source transaction is counted only once per metric, even if both endpoints are selected. Each source row retains its own ingestion identity; identical-looking legitimate rows are not automatically deleted. Multiple selected days for the same account do not repeatedly add its history.

Account IDs follow the existing model's account identifier convention. There is no customer-to-account mapping, so I do not describe account counts as customer counts.

The total-volume denominator is $550,759,935,026.91: all eligible USD activity linked to any account in the test population. The positive-associated denominator is $55,871,612,461.95: eligible USD activity linked to any account with a positive test account-day. Each percentage uses its own denominator. Dollar amounts are activity turnover, not balances, confirmed laundering, recovered funds, or measured review effort.

## Why volume jumps at rank 12

One synthetic account enters through a positive account-day at rank 12. Its 169,756 eligible USD transactions total **$52,762,770,804.54**, accounting for **94.4357%** of the positive-associated denominator. Only 243 of those transactions have a synthetic laundering label; those transactions total **$50,048,709.64**. This verifies the concentration without describing the whole account history as laundering.

At 15,000 account-days, positive-associated volume is $53,882,935,622.97, or 96.4406% of its denominator, while account-day recall is 41.0941%. High dollar coverage and high case coverage are different outcomes.

## Reproduce the aggregates

Required inputs are the original `HI-Small_Trans.csv` and `AML_Tableau_Canonical_389_Positive_Labels.csv`. Large raw transaction and ranking files are not bundled with the website. The canonical ranking must already contain account IDs, dates, labels, scores, and risk ranks; the builder does not refit the model.

```bash
python scripts/build_dashboard_data.py \
  --ranking /path/to/AML_Tableau_Canonical_389_Positive_Labels.csv \
  --transactions /path/to/HI-Small_Trans.csv \
  --output docs
node scripts/check_dashboard.cjs
python -m http.server 8000 --directory docs
```

The builder needs pandas and NumPy. It reconciles every canonical account-day label against the raw transaction labels, checks the key ranking results, and writes input SHA-256 hashes to the output metadata. The static site runs without Python or a backend. GitHub Actions checks the data invariants and controls with Node.js.
