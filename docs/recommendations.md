# Recommendations

This file is completed after the analytical pipeline has produced actual tables. The live recommendation matrix is written to `outputs/tables/recommendation_matrix.csv` and copied into the Tableau extract.

## Decision rule

Priority is assigned from evidence, not from model novelty.

- P1: high expected loss or high PD combined with material exposure
- P2: vintage or data issues that change interpretation
- P3: monitoring and model-risk hygiene

## Required columns

Priority, evidence, business risk, recommendation, action, owner, expected outcome, metric, target, timeline.

## Owners

- Head of Credit: underwriting and policy
- Product Manager: pricing and purpose rules
- Portfolio Manager: exposure and expected-loss dollars
- Risk Analytics: vintage investigation
- Model Risk: monitoring
- Data Team: quality controls
