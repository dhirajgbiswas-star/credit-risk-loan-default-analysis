# Tableau Field Dictionary

| Field | Source extract | Definition |
| --- | --- | --- |
| loan_count | KPI / risk extracts | Number of loans in the grain |
| matured_loan_count | KPI | Loans with a known paid or default outcome |
| funded_amount / ead | KPI / EL | Sum of funded_amnt |
| default_rate | Risk extracts | Defaults / matured loans |
| default_rate_ci_low / high | Risk extracts | Wilson 95% interval |
| charged_off_rate | Risk extracts | Charged-off loans / relevant loans in that table |
| meets_sample_threshold | State extract | False when the state is below the minimum sample size |
| concentration_quadrant | Grade / purpose concentration | Prioritise, Investigate, Optimise, Monitor |
| loan_age_months | Vintage | Months since issue, capped by observation window |
| loans_reached_age | Vintage | Loans old enough to be observed at that age |
| cumulative_default_rate | Vintage | Defaults by that age / loans that reached the age |
| pd | EL extract | Observed matured default rate for the segment |
| lgd_assumption | EL extract | Documented severity assumption |
| expected_loss | EL extract | PD × LGD × EAD |
| expected_loss_pct | EL extract | Expected loss / EAD |
| predicted_pd | Model extract | Model probability on the validation sample |
| risk_band | Model extract | Very Low, Low, Medium, High, Very High |
| priority | Recommendations | P1 immediate, P2 near-term, P3 monitor |

## Calculated fields

```
Default Rate %
[default_rate]

Expected Loss %
[expected_loss] / [ead]

High Risk High Exposure
IF [default_rate] >= {MEDIAN([default_rate])}
AND [funded_amount] >= {MEDIAN([funded_amount])}
THEN "Prioritise" END
```

Risk bands on the model extract are already materialised as `risk_band`.
