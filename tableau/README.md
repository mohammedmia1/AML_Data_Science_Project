# Tableau investigation dashboard

The packaged Tableau Public workbook is an **optional companion** to the primary [interactive case study](../docs/index.html). The canonical test population contains **494,707 synthetic account-days**, with **2,747 reviewed** and **389 positive synthetic labels** among those reviewed (**14.16% precision**, **25.95% recall**, **46.73× lift**).

The portfolio's trained model, metrics and website use the same frozen canonical run. The Tableau workbook should use the accompanying 17-column canonical scored export (`artifacts/aml_tableau_decision_data_canonical.csv` after local reproduction), not a disconnected demonstration dataset. The CSV is not committed due to its size; generate it with `python src/run_canonical.py` or use the separately delivered canonical CSV.

## Verification before declaring the workbook finished

- Open the `.twbx` in Tableau Public and check that it uses **native extracts**, that all dashboard sheets render, and that the investigation queue contains scored account-days.
- Compare the five KPI cards to the figures above and validate the risk score bands and review-outcome composition (**389 selected positives; 2,358 other selected rows**).
- Reconcile any fixed labels, images, tooltips or secondary sources with those figures. Static decoration is fine; charts presented as measured results should be native worksheets or independently validated visualizations.
- Run `python tableau/verify_tableau_csv.py /path/to/aml_tableau_decision_data_canonical.csv` against the scored export.

A working Tableau workbook may be included while design refinement is in progress. The presence of a `.twbx` is **not** proof of independent native-app visual verification. The interactive website is the currently verified presentation.
