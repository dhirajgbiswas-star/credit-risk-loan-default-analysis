# Executive Summary
# Credit Risk & Loan Default Analysis

## Business Situation
Lending institutions need to grow originations without accepting unmanaged credit loss. This review of the Lending Club accepted-loan book measures where default risk and expected loss are concentrated, how vintages perform as loans age, and whether origination-time information can rank higher-risk loans.

## Key Finding 1
The matured book default rate is 20.0% (269,360 defaults on 1,348,099 matured loans). Overall funded amount is $34,004,208,600 across 2,260,701 originated loans.

## Key Finding 2
Credit risk is highly graded. Grade A defaulted at 6.0%, while grade G defaulted at 49.7%.

## Key Finding 3
Purpose and term still differentiate risk after looking at volume. The highest observed purpose-level default rate is small_business at 29.9%.

## Risk Concentration
Management should not look at default rates alone. Large, mid-risk grades can contribute more expected-loss dollars than small, very high-rate niches. Grade-level funded exposure and default rates are both required to set priorities.

## Expected Loss
Using a documented base-case LGD of 50% and the observed matured PD of 20.0%, portfolio expected loss is $1,939,417,186 (10.0% of matured funded exposure). Optimistic and adverse LGD cases are provided in the sensitivity table. These LGD values are analytical assumptions, not official Lending Club metrics.

## Model Performance
The selected origination-time model is hist_gradient_boosting. Validation PR-AUC is 0.38657156286121064 and ROC-AUC is 0.719681863503301. The operating threshold of 0.45 was chosen to minimise expected classification cost.

## Business Judgement
Observed default risk rises sharply as grade weakens: A at 6.0% versus G at 49.7%. Absolute expected loss is still dominated by large grades. Grade C contributes the most base-case expected-loss dollars ($608,129,051), while grade D is the high-rate, high-exposure cell that should be first in the policy queue. 60-month loans defaulted at 32.5%, about twice the shorter-term rate. Newer vintages must be read on an age-adjusted basis; among large matured vintages, 2016 is the weakest at 23.3%.

## Recommendation
1. Review underwriting and pricing for grade D and other Prioritise cells.
2. Set an expected-loss appetite for grade C, which dominates loss dollars.
3. Review 60-month pricing and small-business eligibility.
4. Investigate the 2016 vintage after controlling for grade mix.
5. Use the PD model as a ranking and monitoring tool, not as an automated decline engine.

## Expected Impact
A tighter link between price, policy and observed risk should reduce expected loss percentage in the weakest high-exposure segments and improve risk-adjusted portfolio performance.

## Monitoring
Track Expected Loss $, Expected Loss %, matured default rate, vintage curves at comparable loan age, PR-AUC, Brier score, top-versus-bottom decile default rates, and high-risk/high-exposure segment share.

## Vintage Reference
Best large matured vintage (at least 10,000 matured loans): 2010 at 14.0%. Weakest large matured vintage: 2016 at 23.3%.

## Model Ranking
Validation default rate rises from 3.5% in the lowest predicted-PD decile to 46.9% in the highest decile. Class weighting improves recall and ranking but overstates absolute probabilities, so scores should be used for ordering and review rather than as a calibrated PD for capital.
