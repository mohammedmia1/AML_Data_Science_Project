# Dashboard calculations

I use a frozen account-day ranking to explore review capacity, detection performance, and the USD transaction activity represented in the selected queue. The page loads precomputed aggregate values; it does not train a model in the browser.

## Ranking and cutoff

The canonical CSV contains 494,707 test account-days and 1,499 positive labels. At the original cutoff of 2,747, it captures 389 positives, with precision 14.16%, recall 25.95%, and F1 0.183. The dashboard uses the same canonical account-day ranking as the published model results.

For a prefix of k ranked account-days, I compute precision = TP / k, recall = TP / 1,499, and F1 = 2 × TP / (k + 1,499). Displayed precision is zero for an empty queue. Checking all 494,707 prefixes identifies a unique highest F1 at k = 822: 251 positives and F1 0.216286. This is a retrospective diagnostic, not a newly validated deployment cutoff. The interactive view covers the first 15,000 exact cutoffs, with a first-100 zoom.

## Two amounts for the same review queue

I fix the review snapshot at September 10, 2022, end of day, and include source activity from September 1–10. This is a retrospective account-history snapshot, not a simulation of what was known at an earlier alert timestamp.

1. **Total USD activity to review:** all eligible unique transactions involving at least one account represented in the selected account-day prefix.
2. **Of that, laundering-labeled:** the subset of those same transactions whose raw `Is Laundering` flag equals 1. A positive account-day does not make every transaction in that account’s history positive.

The percentage below the second amount is **laundering-labeled dollars / total selected USD activity**. It answers how much of the selected review amount carries the synthetic label. An empty queue displays zero. Both amounts move with the same slider and use the same accounts, snapshot, currency filter, and transaction identity.

An eligible transaction has both payment and receiving currencies equal to US Dollar. I use amount paid, converted to integer cents before aggregation. No currency conversion is assumed. Incoming and outgoing activity qualify, but a source row enters each metric only once even if both endpoints are selected. Multiple selected days for one account do not repeatedly add its history. Each source row retains its ingestion identity; identical-looking genuine transactions are not automatically removed.

Account IDs follow the existing model convention. There is no customer-to-account mapping, so account counts are not customer counts. Historical laundering-labeled transactions qualify whenever either endpoint enters the selected account set, even if the selected day itself has a negative label. Labels are used for retrospective evaluation, not to select accounts.

## Verified examples

| Review cutoff | Total USD activity | Laundering-labeled subset | Labeled transactions |
|---:|---:|---:|---:|
| 822 | $54,032,936,401.58 | $86,404,704.85 | 482 |
| 2,747 | $60,764,677,637.38 | $148,871,390.41 | 616 |
| 15,000 | $96,190,347,119.06 | $234,818,818.53 | 730 |

At 2,747 selected account-days, the labeled subset is about **0.245%** of total review activity. The count of 616 labeled transactions is different from the model’s 389 positive account-days: these metrics have different units and history windows.

One synthetic account entering at rank 12 contributes **$52,762,770,804.54** of total USD activity. Only **243 transactions totaling $50,048,709.64** carry the synthetic laundering label. This explains the jump in total activity without treating the account’s whole history as laundering. Account identifiers and daily account breakdowns are not published with this dashboard.

For the full eligible test-account population, total USD activity is $550,759,935,026.91. Within that activity, 1,586 laundering-labeled transactions total $1,112,496,564.92. The downloadable CSV additionally reports labeled-dollar coverage against this full-population labeled amount; that coverage is separate from the main card’s share of the selected review amount.

Amounts are synthetic transaction activity, not balances, confirmed criminal proceeds, funds recovered, or measured investigator effort. The review queue is selected by the frozen model ranking; these dollar metrics do not change it.

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
