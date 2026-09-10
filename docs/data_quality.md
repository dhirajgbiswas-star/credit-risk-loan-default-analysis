# Data Quality

## Process

Quality checks run before cleaning and again after the analytical dataset is built.

Dimensions:

- Completeness: missing values and missingness by field
- Validity: interest rates, terms, amounts, DTI and dates
- Uniqueness: duplicate loan IDs and exact duplicate rows
- Consistency: categorical spelling, date formats and loan-status values
- Integrity: funded amount should not exceed requested amount

## Target construction

`loan_status` is not treated as a simple paid-versus-everything-else flag.

| Status | Treatment |
| --- | --- |
| Fully Paid | Non-default, matured |
| Does not meet the credit policy. Status:Fully Paid | Non-default, matured |
| Charged Off | Default, matured |
| Default | Default, matured |
| Does not meet the credit policy. Status:Charged Off | Default, matured |
| Current | Excluded from the binary target |
| Late (16-30 days) | Excluded from the binary target |
| Late (31-120 days) | Excluded from the binary target |
| In Grace Period | Excluded from the binary target |
| Blank | Removed during cleaning |

Default rate numerator: matured defaulted loans.  
Default rate denominator: matured loans only.

## Outputs

- `outputs/tables/schema_report.csv`
- `outputs/tables/data_quality_report.csv`
- `outputs/tables/data_quality_report.html`

## Handling rules

- Raw files are never overwritten.
- Outliers are investigated before any removal. Extreme DTI values are flagged, not deleted automatically.
- Invalid funding relationships are removed because they break a core integrity rule.
- Blank loan-status rows are removed because they cannot support a target.

## Reproduction

```bash
python scripts/run_quality_checks.py
```
