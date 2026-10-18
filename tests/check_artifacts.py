"""Fast, data-free checks for the published model/website contract.

Run from anywhere: python tests/check_artifacts.py
This does not attest to a fresh SQL rebuild or independent Tableau rendering.
"""
from __future__ import annotations
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
metrics = json.loads((ROOT / 'reports/metrics.json').read_text())
curve = json.loads((ROOT / 'docs/capacity.json').read_text())
page = (ROOT / 'docs/index.html').read_text()
rows = curve['rows']

assert len(rows) == 15000
assert [r['k'] for r in rows] == list(range(1, 15001))
assert rows[-1]['tp'] <= metrics['test_positives']
assert all(a['tp'] <= b['tp'] <= a['tp'] + 1 for a, b in zip(rows, rows[1:]))
assert (metrics['train_rows'], metrics['validation_rows'], metrics['test_rows']) == (1534403, 450244, 494707)
assert metrics['test_positives'] == 1499
assert metrics['test_capacity'] == 2747
assert metrics['selected_positives'] == 389
assert math.isclose(metrics['precision'], metrics['selected_positives']/metrics['test_capacity'])
assert math.isclose(metrics['recall'], metrics['selected_positives']/metrics['test_positives'])
assert math.isclose(metrics['lift'], metrics['precision'] / (metrics['test_positives']/metrics['test_rows']))
selected = rows[metrics['test_capacity'] - 1]
assert selected['tp'] == metrics['selected_positives']
for key in ('precision', 'recall', 'lift'):
    assert math.isclose(selected[key], metrics[key], rel_tol=1e-12), key
assert 'data.json' in (ROOT / 'docs/app.js').read_text()
volume = json.loads((ROOT / 'docs/data.json').read_text())
assert volume['meta']['n'] == metrics['test_rows']
assert volume['meta']['positives'] == metrics['test_positives']
assert volume['tp'][0] == 0
assert volume['tp'][1:] == [row['tp'] for row in rows], 'Dashboard ranking differs from published canonical capacity curve'
assert math.isclose(volume['positiveVolume'][12], 52762770804.54)
assert 'id="coverage"' not in page
assert 'First 100' in page
assert '389' in page
assert '397' not in page, 'Old historical figure in the website source'
assert (ROOT / 'models/xgboost_model.json').stat().st_size > 1_000_000
assert (ROOT / 'sql/AML_Portfolio_Pipeline.sql').exists()

# If a full local rerun was performed, it must match the published benchmark.
actual = ROOT / 'artifacts/metrics.json'
if actual.exists():
    rerun = json.loads(actual.read_text())
    for key in ('test_rows', 'test_capacity', 'selected_positives', 'test_positives',
                'precision', 'recall', 'lift', 'roc_auc', 'pr_auc', 'source_file_sha256'):
        assert (math.isclose(rerun[key], metrics[key], rel_tol=1e-10)
                if isinstance(metrics[key], float) else rerun[key] == metrics[key]), key
    rerun_curve = ROOT / 'artifacts/capacity.json'
    if rerun_curve.exists():
        actual_curve = json.loads(rerun_curve.read_text())
        assert actual_curve['rows'] == rows, 'Rerun capacity curve differs from the published one'

print('PASS: published metrics, capacity curve, site references, and model artifact')

