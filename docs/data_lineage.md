# Data Lineage

```
Kaggle Lending Club dataset
        ↓
Raw accepted CSV
        ↓
Validation and schema report
        ↓
Cleaning and type standardisation
        ↓
Target construction and feature engineering
        ↓
Analytical dataset (parquet)
        ↓
Portfolio, risk, vintage and expected-loss tables
        ↓
Origination-time model dataset
        ↓
Predictions and evaluation artefacts
        ↓
Tableau data mart
        ↓
Tableau dashboards
        ↓
Business decision
```

## Systems of record in this project

| Stage | Location |
| --- | --- |
| Raw extract | `data/raw/lending_club/` |
| Analytical dataset | `data/processed/analytical_loans.parquet` |
| Aggregated tables | `outputs/tables/` |
| Figures | `outputs/figures/` |
| Model objects | `outputs/model/` |
| Tableau extracts | `data/processed/tableau/` |
| Executive outputs | `outputs/reports/` |

## Transformations that change grain or meaning

| Step | Grain | Change |
| --- | --- | --- |
| Load | One row per accepted loan | Selected columns only |
| Clean | One row per loan ID | Types, categories, invalid funding rows |
| Target | Same | Matured flag and binary default |
| Features | Same | Ratios, buckets, vintage and loan age |
| Risk tables | One row per segment | Rates on matured loans |
| Model | One row per matured loan | Origination features only |
| Tableau | Aggregates and scored sample | Dashboard-ready names |

## Ownership

- Data owner: Credit Risk / Lending business owner
- Data steward: Risk Analytics
- Technical owner: Analytics Engineering
