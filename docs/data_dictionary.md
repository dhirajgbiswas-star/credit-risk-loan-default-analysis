# Data Dictionary

Field names follow the accepted Lending Club extract. Only fields used in this project are documented here.

## Identifiers and origination

| Field | Type | Grain | Definition | Model use |
| --- | --- | --- | --- | --- |
| id | string | Loan | Lending Club loan identifier | Excluded |
| loan_amnt | numeric | Loan | Requested loan amount | Included |
| funded_amnt | numeric | Loan | Amount funded. Used as EAD | Excluded from PD model; used in EL |
| term / term_months | numeric | Loan | 36 or 60 month contractual term | Included |
| int_rate | numeric | Loan | Interest rate at origination | Included |
| installment | numeric | Loan | Scheduled monthly instalment | Included |
| grade / sub_grade | category | Loan | Assigned Lending Club grade | Grade included |
| emp_length / emp_length_years | numeric | Loan | Self-reported employment length | Included |
| home_ownership | category | Loan | Rent, mortgage, own or other | Included |
| annual_inc | numeric | Loan | Self-reported annual income | Included |
| verification_status | category | Loan | Income verification status | Included |
| issue_d | date | Loan | Origination month | Vintage only |
| purpose | category | Loan | Stated loan purpose | Included |
| addr_state | category | Loan | Borrower state | Portfolio only |
| zip_code | category | Loan | Masked three-digit zip | Excluded |
| dti | numeric | Loan | Debt-to-income ratio | Included |
| delinq_2yrs | numeric | Loan | Delinquencies in prior 24 months | Included |
| earliest_cr_line | date | Loan | Oldest credit line | Used to build credit history |
| fico_range_low | numeric | Loan | Lower FICO bound at origination | Included |
| inq_last_6mths | numeric | Loan | Recent credit inquiries | Included |
| open_acc | numeric | Loan | Open credit lines | Included |
| pub_rec | numeric | Loan | Public records | Included |
| revol_util | numeric | Loan | Revolving utilisation | Included |
| total_acc | numeric | Loan | Total credit lines | Included |
| application_type | category | Loan | Individual or joint | Included |
| pub_rec_bankruptcies | numeric | Loan | Bankruptcy records | Included |

## Outcome and leakage fields

| Field | Type | Decision-time availability | Treatment |
| --- | --- | --- | --- |
| loan_status | category | After performance is observed | Target construction only |
| last_pymnt_d | date | After origination | Vintage timing only |
| recoveries | numeric | After default | Recovery estimate only |
| total_pymnt | numeric | After origination | Excluded from PD model |
| out_prncp | numeric | After origination | Excluded from PD model |
| debt_settlement_flag | category | After origination | Excluded from PD model |

## Engineered fields

| Field | Formula or rule | Business meaning |
| --- | --- | --- |
| is_matured | Status in paid or default families | Loan has a known binary outcome |
| is_default | 1 if charged off or default | Binary credit-risk target |
| loan_to_income | loan_amnt / annual_inc | Affordability |
| installment_to_income | installment / (annual_inc / 12) | Payment burden |
| credit_history_years | Months from earliest credit line to issue date / 12 | Credit seasoning |
| vintage | Issue year | Cohort |
| loan_age_months | Months from issue date to last payment or snapshot | Development age |
| income_bucket, dti_bucket, interest_rate_bucket, loan_amount_bucket | Evidence-oriented bins | Segmentation |

## KPI dictionary

| KPI | Definition | Formula | Numerator | Denominator | Business meaning |
| --- | --- | --- | --- | --- | --- |
| Default Rate | Share of matured loans that defaulted | Defaults / Matured loans | Charged off, Default, and credit-policy charged-off loans | Fully paid and defaulted loans | Portfolio credit risk |
| Charged-Off Rate | Share of originated loans that charged off | Charged-off loans / Originated loans | Charged-off statuses | All loaded originated loans | Realised severe loss incidence |
| Funded Amount | Total principal funded | SUM(funded_amnt) | Funded amount | Not a rate | Exposure |
| Average Loan | Mean requested amount | AVG(loan_amnt) | Loan amount | Loan count | Typical ticket size |
| PD | Probability of default | Observed matured default rate or model output | Defaults or predicted probability | Matured loans or scored loans | Forward-looking or observed likelihood |
| LGD | Loss after recovery | Assumed 40/50/60% or 1 - recovery rate | Loss | EAD | Severity assumption |
| EAD | Exposure at default | Funded amount in this study | funded_amnt | Loan or segment | Amount exposed |
| Expected Loss $ | Expected credit loss | PD × LGD × EAD | Product of the three terms | Not a rate | Potential loss |
| Expected Loss % | Loss relative to exposure | Expected Loss $ / EAD | Expected loss | Funded exposure | Risk-adjusted efficiency |
| Recovery Rate | Recoveries on defaulted loans | recoveries / funded_amnt | Recoveries | Defaulted funded amount | Analytical recovery estimate |
