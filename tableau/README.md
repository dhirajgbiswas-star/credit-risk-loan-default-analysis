# Tableau Workbooks

This folder contains Tableau workbook files (`.twb`) connected to the project extracts in `data/processed/tableau/`.

## Files

| Workbook | Contents |
| --- | --- |
| `Credit_Risk_Loan_Default_Analysis.twb` | Master workbook with all six dashboards |
| `dashboard_01_executive_risk_overview.twb` | Dashboard 1 only |
| `dashboard_02_credit_risk_segmentation.twb` | Dashboard 2 only |
| `dashboard_03_vintage_performance.twb` | Dashboard 3 only |
| `dashboard_04_expected_loss_concentration.twb` | Dashboard 4 only |
| `dashboard_05_default_probability_model.twb` | Dashboard 5 only |
| `dashboard_06_decision_recommendations.twb` | Dashboard 6 only |

## Open in Tableau

1. Install [Tableau Desktop](https://www.tableau.com/products/desktop) or Tableau Public.
2. Open `Credit_Risk_Loan_Default_Analysis.twb` (or one of the individual dashboard files).
3. If prompted, confirm the CSV connections in `data/processed/tableau/`.
4. Use the dashboard tabs at the bottom to move between the six views.

The workbooks are Tableau Desktop XML (`version="18.1"`). They connect directly to the CSV extracts using relative paths. Keep the `tableau/` and `data/processed/tableau/` folders in the same project structure.

## Dashboard specification

Layout, KPI definitions, filters and insight requirements are documented in `dashboard_specification.md`.

## Notes

- KPI cards on Dashboard 1 are rendered as dashboard text using values from `tableau_kpi_summary.csv`.
- Each dashboard includes an insight block with evidence drawn from the project analysis.
- After opening a workbook, you can refine colours, tooltips, filters and navigation actions in Tableau Desktop.
