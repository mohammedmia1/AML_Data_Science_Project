"""Validate canonical outputs against published contract."""
import json, math, os
from pathlib import Path
base = Path(__file__).resolve().parents[1]
published = json.loads((base / 'reports/metrics.json').read_text())
curve = json.loads((base / 'docs/capacity.json').read_text())
assert len(curve['rows']) == 15000
assert [r['k'] for r in curve['rows']] == list(range(1, 15001))
assert all(curve['rows'][i]['tp'] <= curve['rows'][i+1]['tp'] for i in range(len(curve['rows'])-1))
assert published['test_rows'] == 494707
assert published['test_capacity'] == 2747
assert published['selected_positives'] == 389
assert published['test_positives'] == 1499
assert curve['rows'][published['test_capacity']-1]['tp'] == published['selected_positives']
for name in ('precision','recall','lift'):
    assert math.isclose(curve['rows'][2746][name], published[name], rel_tol=1e-12)
actual_path = base / 'artifacts/metrics.json'
if actual_path.exists():
    actual = json.loads(actual_path.read_text())
    for name in ('test_rows','test_capacity','selected_positives','test_positives','precision','recall','lift','roc_auc','pr_auc','source_file_sha256'):
        assert actual[name] == published[name], (name, actual[name], published[name])
print('PASS: canonical metric and capacity contract')
