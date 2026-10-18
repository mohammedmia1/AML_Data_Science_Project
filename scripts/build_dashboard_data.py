"""Precompute exact review-prefix metrics without fitting or changing the model.

Account histories use a fixed Sep 10 retrospective snapshot. Amounts are USD
payment-side transaction activity, not balances or confirmed laundered funds.
Each original source row has one ingestion identity; min rank across its two
endpoints makes the transfer enter each cumulative metric exactly once.
"""
from pathlib import Path
import json
import argparse
import hashlib
import numpy as np
import pandas as pd

parser=argparse.ArgumentParser(description='Build aggregate AML dashboard data from a canonical ranking and raw synthetic transactions.')
parser.add_argument('--ranking',type=Path,required=True)
parser.add_argument('--transactions',type=Path,required=True)
parser.add_argument('--output',type=Path,default=Path('docs'))
args=parser.parse_args()
args.output.mkdir(parents=True,exist_ok=True)
def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()
c=pd.read_csv(args.ranking,dtype={'account_id':str}).sort_values('risk_rank')
n=len(c); labels=c.has_laundering_tx.to_numpy(dtype=int); pos=int(labels.sum())
first=c.groupby('account_id').risk_rank.min()
positive=c[c.has_laundering_tx.eq(1)].groupby('account_id').risk_rank.min()
total=np.zeros(n+2,dtype=np.int64); txn_counts=total.copy(); labeled_volume=total.copy(); labeled_counts=total.copy()
raw_labels={}; usd_rows=0; eligible_rows=0; source_rows=0
for t in pd.read_csv(args.transactions,dtype={'Account':str,'Account.1':str},chunksize=250000):
    source_rows+=len(t)
    days=t.Timestamp.str.slice(0,10).str.replace('/','-')
    check=t.loc[days.isin(['2022-09-09','2022-09-10']) & t['Is Laundering'].eq(1)]
    for ix,row in check.iterrows():
        raw_labels[(row['Account'],days.loc[ix])]=1
        raw_labels[(row['Account.1'],days.loc[ix])]=1
    before=days.le('2022-09-10') & days.ge('2022-09-01')
    eligible_rows+=int(before.sum())
    t=t.loc[before & t['Payment Currency'].eq('US Dollar') & t['Receiving Currency'].eq('US Dollar')]
    usd_rows+=len(t)
    a=t.Account.map(first).fillna(n+1).to_numpy(dtype=int)
    b=t['Account.1'].map(first).fillna(n+1).to_numpy(dtype=int)
    ranks=np.minimum(a,b)
    cents=np.rint(t['Amount Paid'].to_numpy()*100).astype(np.int64)
    np.add.at(total,ranks,cents)
    np.add.at(txn_counts,ranks,1)
    is_labeled=t['Is Laundering'].to_numpy(dtype=int)
    np.add.at(labeled_volume,ranks,cents*is_labeled)
    np.add.at(labeled_counts,ranks,is_labeled)

actual=np.array([raw_labels.get((a,d),0) for a,d in zip(c.account_id,c.activity_date)])
assert np.array_equal(labels,actual), 'Raw labels do not reconcile'
tp=np.r_[0,np.cumsum(labels)]
k=np.arange(n+1); f1=2*tp/(k+pos)
assert int(np.argmax(f1))==822 and int(tp[2747])==389
total=total.cumsum(); txn_counts=txn_counts.cumsum()
labeled_volume=labeled_volume.cumsum(); labeled_counts=labeled_counts.cumsum()
assert np.all(labeled_volume<=total)
assert np.all(labeled_counts<=txn_counts)
accounts=np.bincount(first.to_numpy(),minlength=n+2).cumsum()
positive_accounts=np.bincount(positive.to_numpy(),minlength=n+2).cumsum()
limit=15000
out={'meta':{'n':n,'positives':pos,'bestK':822,'defaultK':2747,'limit':limit,'historyStart':'2022-09-01','asOf':'2022-09-10','sourceRows':source_rows,'historyRows':eligible_rows,'usdHistoryRows':usd_rows,'eligibleVolume':int(total[n])/100,'eligibleLabeledVolume':int(labeled_volume[n])/100,'eligibleLabeledTransactions':int(labeled_counts[n]),'eligibleAccounts':len(first),'eligiblePositiveAccounts':len(positive),'labelReconciliation':True,'rankingSHA256':digest(args.ranking),'transactionsSHA256':digest(args.transactions)},'tp':tp[:limit+1].tolist(),'volume':(total[:limit+1]/100).tolist(),'transactions':txn_counts[:limit+1].tolist(),'labeledVolume':(labeled_volume[:limit+1]/100).tolist(),'labeledTransactions':labeled_counts[:limit+1].tolist(),'accounts':accounts[:limit+1].tolist(),'positiveAccounts':positive_accounts[:limit+1].tolist()}
(args.output/'data.json').write_text(json.dumps(out,separators=(',',':')))
(args.output/'dashboard_verification.json').write_text(json.dumps({'meta':out['meta'],'checkpoints':{str(j):{'tp':int(tp[j]),'f1':float(f1[j]),'volume':int(total[j])/100,'labeledVolume':int(labeled_volume[j])/100,'labeledTransactions':int(labeled_counts[j]),'accounts':int(accounts[j])} for j in [822,2747,15000]}},indent=2))
print((args.output/'dashboard_verification.json').read_text())
