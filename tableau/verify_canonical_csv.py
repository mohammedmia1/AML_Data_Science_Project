"""Independently audit the full canonical scored CSV using only Python stdlib."""
from __future__ import annotations
import csv
import math
import sys
from pathlib import Path

if len(sys.argv) != 2:
    raise SystemExit('Usage: python tableau/verify_canonical_csv.py PATH_TO_CANONICAL_CSV')
source=Path(sys.argv[1]); assert source.exists(),source
rows=0;positives=0;selected=0;selected_pos=0;rankset=set()
with source.open(newline='') as f:
    reader=csv.DictReader(f)
    needed={'account_id','activity_date','risk_rank','risk_score','has_laundering_tx','selected_for_review','model_outcome'}
    assert needed.issubset(reader.fieldnames), needed.difference(reader.fieldnames)
    for r in reader:
        rows+=1
        pos=int(r['has_laundering_tx']);is_sel=int(r['selected_for_review']);rank=int(r['risk_rank'])
        assert pos in (0,1) and is_sel in (0,1)
        assert rank not in rankset, f'duplicate rank: {rank}'
        rankset.add(rank)
        assert is_sel==(rank<=2747), f'selection/rank mismatch: {rank}'
        positives+=pos;selected+=is_sel;selected_pos+=is_sel*pos
        expected=('True Positive' if pos and is_sel else 'False Positive' if is_sel else 'False Negative' if pos else 'True Negative')
        assert r['model_outcome']==expected,(rank,r['model_outcome'],expected)
assert len(rankset)==rows and min(rankset)==1 and max(rankset)==rows
assert (rows,positives,selected,selected_pos)==(494707,1499,2747,389), (rows,positives,selected,selected_pos)
print(f'PASS: {rows:,} unique ranked account-days; {selected:,} reviewed; {selected_pos:,} selected positives; precision {selected_pos/selected:.2%}; recall {selected_pos/positives:.2%}')
