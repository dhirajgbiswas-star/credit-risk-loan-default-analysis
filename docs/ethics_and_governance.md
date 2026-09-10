# Ethics and Governance

## Data ethics principles

### Purpose limitation

The dataset is used only for legitimate analytical and educational portfolio-risk analysis. It is not used to make live credit decisions about identified people.

### Data minimisation

The project loads the accepted-loan fields required for portfolio, risk, vintage, expected-loss and origination-time modelling work. Free-text employment titles, URLs and narrative descriptions are not used in the model.

### Privacy

Raw loan-level files are excluded from Git. Zip codes are already masked. Outputs intended for sharing are aggregated or limited to model-evaluation extracts.

### Fairness

State, zip code and free-text employment fields can act as proxies. They are used for portfolio description where relevant and are excluded from the primary probability-of-default model. This study does not recommend lending rules based on protected characteristics.

### Transparency

Target definitions, leakage exclusions, LGD assumptions and model limitations are written down. Assumed LGD values are not presented as official Lending Club metrics.

### Human oversight

Model scores are decision-support. They are not an automated approve-or-decline engine.

### Explainability

Logistic coefficients, tree importance and permutation importance are provided so risk drivers can be discussed in business language. Associations are predictive, not causal.

### Monitoring

A production process would monitor drift, calibration, discrimination, stability and changing portfolio mix. This repository provides the tables needed to start that conversation.

## Governance controls

| Control | Implementation |
| --- | --- |
| Data owner | Credit Risk / Lending business owner |
| Data steward | Risk Analytics |
| Technical owner | Analytics Engineering |
| Lineage | `docs/data_lineage.md` |
| Dictionary | `docs/data_dictionary.md` |
| Source documentation | `data/README.md` |
| Quality rules | `src/data/validate.py` and `outputs/tables/data_quality_report.csv` |
| Access | Local raw files, credentials via environment or `~/.kaggle/kaggle.json` |
| Retention | Raw files remain local and uncommitted |
| Versioning | Model objects and training summary under `outputs/model/` |
| Auditability | Scripts are runnable from the project root |
| Reproducibility | Fixed random seed, documented commands |
| Model documentation | `docs/model_card.md` |

## Model risk

The model is an educational ranking tool trained on historical marketplace loans. Economic conditions, underwriting policy and borrower mix have changed since 2018. Scores should not be interpreted as a production IRB or IFRS 9 PD.

## Responsible lending

Recommendations concern portfolio investigation, pricing review and monitoring. They do not instruct an automated decline of an individual applicant.
