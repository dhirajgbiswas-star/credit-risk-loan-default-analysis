# Tableau Dashboard Specification

## Design principles

Clear hierarchy, limited colours, meaningful titles, filters at the top, KPI cards, tooltips that define the metric, and an insight block on every page. Every chart answers a business question.

Each dashboard must show:

- Key insight
- Evidence
- Business meaning
- Recommended action

Populate those four lines from `outputs/reports/executive_summary.md` and the recommendation matrix after the pipeline has run. Do not type placeholder percentages into Tableau.

## Dashboard 1 — Executive Risk Overview

Business question: How large is the book, what is the matured default rate, and where is expected loss concentrated?

KPI cards: Funded Amount, Loan Count, Default Rate, Charged-Off Rate, Expected Loss $, Expected Loss %, Average PD.

Charts:

- Portfolio trend by issue year
- Default rate by year using matured loans
- Expected loss by grade
- Risk concentration matrix
- Top risk segments

Filters: Issue Year, Grade, Purpose, State, Loan Term.

## Dashboard 2 — Credit Risk Segmentation

Business question: Which grades, purposes, terms, incomes and DTI bands drive observed default?

Charts: default rate by grade, purpose, term, DTI and income; exposure by risk segment; expected loss by segment. Use conditional highlighting for cells above the portfolio default rate.

## Dashboard 3 — Vintage Performance

Business question: Which vintages are underperforming and when does risk emerge?

Charts: vintage curves, vintage heatmap, cumulative default rate, cumulative loss, loan-age analysis.

Filters: vintage, grade, purpose, term.

Use `loans_reached_age` as the denominator so immature vintages are not compared unfairly.

## Dashboard 4 — Expected Loss and Portfolio Concentration

Business question: Where should management focus first?

Charts: expected loss by grade, purpose, state and vintage; PD × exposure matrix; high-risk/high-exposure segments.

This is the PD × Exposure × Expected Loss view. A high-rate, low-balance cell is Investigate. A high-rate, high-balance cell is Prioritise.

## Dashboard 5 — Default Probability Model

Business question: Can origination-time information rank higher-risk loans, and are the probabilities usable?

Charts: predicted PD distribution, actual versus predicted default rate, calibration curve, precision-recall curve, feature importance, risk deciles, threshold analysis.

Risk bands: Very Low, Low, Medium, High, Very High.

## Dashboard 6 — Decision and Recommendation

Business question: What should happen next, who owns it, and how will we know it worked?

Columns: Priority, Recommended Action, Owner, Expected Outcome, KPI, Evidence, Current Status.

Navigation: finding → recommendation → owner → metric.

## Interactivity

- Global filters on dashboards 1–4
- Highlight action from grade or purpose bars to expected-loss detail
- Filter action from a recommendation row to the related segment
- Reset-filters button
- Navigation buttons across the six dashboards
- Dynamic titles that include the filtered default rate where practical

## Implementation order

1. Connect to the CSV extracts in `data/processed/tableau/`
2. Create a relationship between grade-level risk and grade-level expected loss on `grade`
3. Build KPI cards from `tableau_kpi_summary.csv`
4. Build the concentration scatter with default rate on Y and funded amount on X
5. Build vintage curves from `tableau_vintage.csv`
6. Add the recommendation table last so owners and metrics stay aligned with the evidence
