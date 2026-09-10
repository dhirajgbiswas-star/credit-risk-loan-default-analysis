# Analytical Framework

```
Business problem
        ↓
Business questions
        ↓
Data requirements
        ↓
Data quality
        ↓
Exploratory analysis
        ↓
Risk segmentation
        ↓
Vintage analysis
        ↓
Expected loss
        ↓
Default probability model
        ↓
Business judgement
        ↓
Decision
        ↓
Action
        ↓
Monitoring
```

Every major exhibit is expected to end in a decision, an owner and a metric.

## Layer 1 — Portfolio analytics

Volume, funded amount, average loan size, interest rate, income, term, grade, purpose, employment, geography and borrower characteristics.

## Layer 2 — Credit risk analytics

Default and charge-off behaviour by grade, purpose, state, income, DTI, term, interest rate, employment length and loan amount. High-risk and high-exposure cells are highlighted together.

## Layer 3 — Vintage analysis

Cohorts are defined by issue year. Performance is measured at comparable loan age so newer vintages are not compared with fully matured vintages on an unadjusted default rate.

## Layer 4 — Expected loss

```
Expected Loss = PD × LGD × EAD
```

- PD is the observed default rate on matured loans in the segment, or the model PD when used for ranking.
- LGD is an analytical assumption, stress-tested at 40%, 50% and 60%. Where recoveries exist, an implied recovery rate is reported separately and is not treated as an official Lending Club LGD.
- EAD is funded amount at origination for this study.

## Layer 5 — Default probability model

A classification model uses only information that would be available at origination. Current, late and in-grace loans are excluded from the binary target because their final outcome is not known.

## Business judgement format

```
Observation
    ↓
Evidence
    ↓
Interpretation
    ↓
Business risk
    ↓
Decision
    ↓
Action
    ↓
Metric
```

## Decision quadrants

```
                     HIGH EXPECTED LOSS
                           ↑
                           |
       INVESTIGATE         |       PRIORITISE
                           |
LOW EXPOSURE --------------+-------------- HIGH EXPOSURE
                           |
       MONITOR             |       OPTIMISE
                           |
                           ↓
                     LOW EXPECTED LOSS
```
