"""Check saved notebook results against the published evaluation numbers.

No Jupyter kernel or large training data is needed for this check.
The check validates saved evidence, not full model reproducibility.
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
notebook_path = ROOT / "notebooks" / "AML_Model_Development.ipynb"
metrics_path = ROOT / "reports" / "metrics.json"

notebook = json.loads(notebook_path.read_text(encoding="utf-8"))
metrics = json.loads(metrics_path.read_text(encoding="utf-8"))

code_cells = [cell for cell in notebook["cells"] if cell["cell_type"] == "code"]
assert len(code_cells) == 7, "Expected seven code cells"
assert all(cell.get("outputs") for cell in code_cells), "Notebook output is missing"

# Jupyter captures print statements as stream outputs.
printed_text = "\n".join(
    "".join(output.get("text", []))
    for cell in code_cells
    for output in cell["outputs"]
    if output.get("output_type") == "stream"
)

# These are independently measured *validation* figures, not test metrics.
validation_values = [
    "Logistic regression validation PR-AUC: 0.0378",
    "XGBoost validation PR-AUC: 0.1286",
    "0.7995", "0.8446", "170", "383", "0.0680", "0.1532",
]
for value in validation_values:
    assert value in printed_text, f"Missing validation evidence: {value}"

# Confirm the held-out figures agree with the committed canonical metrics.
for label, expected in [
    ("Test account-days", str(metrics["test_rows"])),
    ("Review slots", str(metrics["test_capacity"])),
    ("Positive labels selected", str(metrics["selected_positives"])),
]:
    matching_line = next((line for line in printed_text.splitlines() if label in line), "")
    assert expected in matching_line, f"Saved output disagrees with metrics.json: {label}"

print("PASS: saved notebook outputs and canonical summary are consistent")
