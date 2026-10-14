"""Check the exported canonical Tableau CSV before replacing the legacy extract."""
import argparse
from pathlib import Path
import pandas as pd

parser = argparse.ArgumentParser()
parser.add_argument('csv_path', type=Path)
a = parser.parse_args()
expected = ['account_id','activity_date','transaction_count','outgoing_ratio','total_sent',
 'total_received','avg_transaction_amount','max_transaction_amount','unique_counterparties',
 'unique_banks','currency_diversity','rapid_transaction_ratio','has_laundering_tx',
 'risk_score','risk_rank','selected_for_review','model_outcome']
df = pd.read_csv(a.csv_path, dtype={'account_id':str})
assert list(df) == expected, (list(df),expected)
assert len(df) == 494707, len(df)
assert df['risk_rank'].is_unique and df['risk_rank'].min()==1 and df['risk_rank'].max()==len(df)
assert not df[['account_id','activity_date']].duplicated().any()
selected = df.loc[df['selected_for_review']==1]
assert len(selected) == 2747, len(selected)
assert selected['risk_rank'].max() == 2747
assert (df['has_laundering_tx']==1).sum() == 1499
assert selected['has_laundering_tx'].sum() == 389
assert abs(selected['has_laundering_tx'].mean() - 0.14160902803) < 1e-9
assert abs(389/1499 - 0.25950633755) < 1e-9
print('PASS: Tableau canonical CSV fields, ranks, account-day uniqueness, queue and metrics')
