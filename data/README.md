# Data

## Source

Primary dataset: **Lending Club Loan Data** on Kaggle.

- Dataset page: https://www.kaggle.com/datasets/wordsforthewise/lending-club
- Coverage: accepted and rejected loan applications from 2007 through 2018 Q4
- This project uses the accepted-loan file as the primary analytical source because it contains funded amounts, loan status and performance fields required for default, vintage and expected-loss analysis.

The dataset must be downloaded under Kaggle’s current terms and licence. This repository does not redistribute the raw files.

## Expected layout

```
data/
  raw/
    lending_club/
      accepted_2007_to_2018Q4.csv
      rejected_2007_to_2018Q4.csv
  processed/
    analytical_loans.parquet
    tableau/
  external/
```

Compressed `.csv.gz` files in the same folder are also accepted.

If the Kaggle extract is already stored in the project `archive/` folder, `python scripts/download_data.py` will locate it and stage it under `data/raw/lending_club/`.

## File size

Approximate sizes from the public extract:

| File | Rows | Size |
| --- | --- | --- |
| accepted_2007_to_2018Q4.csv | about 2.26 million | about 1.6 GB uncompressed |
| rejected_2007_to_2018Q4.csv | about 27.6 million | larger than the accepted file |

## Download

Option 1 — Kaggle website:

1. Accept the dataset terms on Kaggle.
2. Download the archive.
3. Extract the accepted and rejected CSV files into `data/raw/lending_club/`.

Option 2 — Kaggle CLI:

```bash
kaggle datasets download -d wordsforthewise/lending-club
```

Then unzip the archive into `data/raw/lending_club/`.

Option 3 — project helper:

```bash
python scripts/download_data.py
```

The helper uses the official Kaggle configuration. Set `KAGGLE_USERNAME` and `KAGGLE_KEY` as environment variables or use `~/.kaggle/kaggle.json`. Do not place credentials in the repository.

## Why raw data is excluded from Git

The raw extract is large, is licensed by Kaggle, and can contain borrower-level fields that should not be published in a public repository. Only code, documentation and aggregated outputs belong in version control.

## Data dictionary

A project-specific dictionary is maintained in `docs/data_dictionary.md`. It covers the fields used in analysis and modelling, not every column in the 151-field accepted-loan file.

## Licensing and use

Use the dataset only for legitimate analytical and educational work consistent with Kaggle’s terms and the original data provider’s restrictions. Do not attempt to re-identify borrowers. Zip codes in the file are already masked to the first three digits.
