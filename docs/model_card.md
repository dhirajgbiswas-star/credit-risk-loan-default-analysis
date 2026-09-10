# Model Card

## Model purpose

Estimate a probability of default for Lending Club loans using information that would be available at origination, so higher-risk loans can be ranked and monitored.

## Intended use

- Portfolio ranking
- Segment challenge and monitoring
- Threshold discussion for enhanced review

## Out-of-scope use

- Automated approval or decline of an individual applicant
- Regulatory capital or accounting PD
- Causal statements about why a borrower defaulted
- Use of geography or free-text employment as a scoring input

## Training data

Accepted Lending Club loans with a matured outcome: Fully Paid, Charged Off, Default, and the corresponding “does not meet the credit policy” statuses. Current, late and in-grace loans are excluded.

## Target definition

- Default = 1: Charged Off, Default, Does not meet the credit policy. Status:Charged Off
- Non-default = 0: Fully Paid, Does not meet the credit policy. Status:Fully Paid

## Features

Origination amount, term, interest rate, instalment, grade, employment length, home ownership, income, verification status, purpose, DTI, recent delinquency, FICO, inquiries, utilisation, account counts, application type, bankruptcies, credit-history length, loan-to-income and instalment-to-income.

## Leakage controls

Payment, recovery, settlement, hardship, outstanding principal and current loan-status fields are excluded from the model. The assessment is stored in `outputs/tables/feature_leakage_assessment.csv`.

## Class imbalance

Defaults are the minority class. Training uses class weights and a stratified train/test split. Accuracy is not the primary metric.

## Model architecture

Three candidates are trained:

1. Logistic regression
2. Random forest
3. Histogram-based gradient boosting

The champion is selected on validation PR-AUC, with calibration, Brier score and expected-cost thresholding reviewed before use.

## Evaluation metrics

ROC-AUC, PR-AUC, precision, recall, F1, Brier score, confusion matrix, decile ordering and calibration.

## Threshold

The operating threshold minimises expected cost using a documented false-negative to false-positive cost ratio of 5:1. The ratio is an analytical assumption and can be replaced with a finance-approved cost model.

## Interpretability

Logistic coefficients, native feature importance and permutation importance are produced. Language used in commentary is “associated with higher predicted default risk”, not “causes default”.

## Fairness considerations

State, zip code and employment title are excluded from scoring. Grade and purpose remain business attributes and should still be reviewed for proxy effects if used in policy.

## Limitations

Historical marketplace loans through 2018, incomplete recoveries, class imbalance, vintage maturity differences and the absence of causal identification. See the limitations section in the README.

## Monitoring

PR-AUC, Brier score, calibration, decile lift, population stability and segment default rates.

## Version

1.0.0
