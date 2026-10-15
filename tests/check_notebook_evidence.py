"""Verify saved notebook evidence, not a new end-to-end model training run."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
nb=json.loads((ROOT/'notebooks/AML_Model_Development.ipynb').read_text())
metrics=json.loads((ROOT/'reports/metrics.json').read_text())
cells=[c for c in nb['cells'] if c['cell_type']=='code']
assert len(cells)==9, 'Expected nine guided code cells'
assert all(c.get('outputs') for c in cells), 'Missing saved notebook output'

def cell_source(c):return ''.join(c['source'])
def saved_text(c):
    lines=[]
    for out in c['outputs']:
        data=out.get('data',{})
        for x in [out.get('text',[]),data.get('text/plain',[]),data.get('text/html',[])]:
            lines.append(''.join(x) if isinstance(x,list) else str(x))
    return '\n'.join(lines)

def find_code(fragment):
    return next(c for c in cells if fragment in cell_source(c))

inspection=saved_text(find_code('Duplicate account-days:'))
for value in ['2479354','7131','Duplicate account-days: 0']:
    assert value in inspection, 'Dataset inspection missing '+value
split=saved_text(find_code('Train, validation, test:')) if any('Train, validation, test:' in cell_source(c) for c in cells) else '\n'.join(saved_text(c) for c in cells)
for value in ['1534403','450244','494707']:
    assert value in split, 'Chronological split missing '+value
comparison=saved_text(find_code('count_positives_at_budget'))
for value in ['0.0378','0.1286','0.7995','0.8446','170','383','6.80%','15.32%']:
    assert value in comparison, 'Missing validation comparison '+value
chart=find_code('ax.barh')
assert 'image/png' in chart['outputs'][0].get('data',{}),'Missing saved model-comparison chart'
assert 'baseline_found, xgb_found' in cell_source(chart),'Chart must read from measured comparison variables'
test=saved_text(find_code('results = pd.DataFrame'))
for value in [f'{metrics["test_rows"]:,}',f'{metrics["test_capacity"]:,}',f'{metrics["selected_positives"]:,}',f'{metrics["selected_positives"]/metrics["test_capacity"]:.2%}',f'{metrics["selected_positives"]/1499:.2%}','46.73×']:
    assert value in test,'Missing published held-out value '+value
assert any('How we verified the project' in ''.join(c['source']) for c in nb['cells'] if c['cell_type']=='markdown')
print('PASS: saved notebook results, comparison chart and canonical numbers are consistent')
