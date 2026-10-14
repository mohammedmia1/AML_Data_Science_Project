# Applying the portfolio quality update

This update is designed for `mohammedmia1/AML_Data_Science_Project` and **does not replace the working Tableau workbook**. It adds the full SQL feature-engineering pipeline and automated result checks, fixes the runnable pipeline's capacity JSON output, and improves README and Tableau documentation.

## Apply using GitHub Desktop

1. Open GitHub Desktop with `AML_Data_Science_Project` selected. Choose **Repository → Show in Finder**.
2. Extract `AML_Portfolio_Quality_Update.zip` to a separate Downloads folder.
3. Copy **the contents** of `AML_Portfolio_Quality_Update` into the cloned repository root; approve replacing same-named text files. Keep existing folders and all files not in this package.
4. Return to GitHub Desktop, review the changes, commit as `Validate canonical pipeline and integrate SQL`, then click **Push origin**.
5. On GitHub, open **Actions → Validate published artifacts**. Check for a green passing run.

You may separately add your existing verified Tableau companion under `tableau/AML_Investigation_Prioritization_Dashboard.twbx` when ready. This package intentionally does not include or modify that large binary file.

## What was checked independently

- `python tests/check_artifacts.py` — passed against the published canonical metrics and website curve.
- `python tableau/verify_canonical_csv.py <scored_export.csv>` — passed for 494,707 rows, 2,747 selected rows, 389 selected positives, unique ranks, and outcomes.
- All 15,000 website capacity points exactly matched sorted labels from the canonical scored CSV.
- Python scripts compiled.
- Source SQL reviewed structurally, **not rerun against raw transactions**.
- Tableau Public rendered the previous working workbook, but no new workbook was rendered as part of this update.

Do not delete the existing local project files. This is an overlay, not a replacement repository.
