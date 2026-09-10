"""Load Lending Club files using the observed schema."""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from src.config import ACCEPTED_FILENAME, ANALYSIS_COLUMNS, RAW_DIR, TABLE_DIR
from src.data.download import find_local_file, prepare_raw_data

logger = logging.getLogger(__name__)


def resolve_accepted_path() -> Path:
    prepare_raw_data(allow_download=False)
    path = find_local_file(ACCEPTED_FILENAME)
    if path is None:
        raise FileNotFoundError(
            f"{ACCEPTED_FILENAME} was not found. Place the Kaggle extract in "
            f"{RAW_DIR} or the project archive folder."
        )
    return path


def load_accepted_loans(
    columns: list[str] | None = None,
    nrows: int | None = None,
) -> pd.DataFrame:
    path = resolve_accepted_path()
    usecols = columns or ANALYSIS_COLUMNS
    logger.info("Loading accepted loans from %s", path)
    frame = pd.read_csv(
        path,
        usecols=lambda col: col in set(usecols),
        nrows=nrows,
        low_memory=False,
    )
    missing = [col for col in usecols if col not in frame.columns]
    if missing:
        logger.warning("Requested columns were not present in the file: %s", missing)
    logger.info("Loaded %s rows and %s columns", f"{len(frame):,}", frame.shape[1])
    return frame


def write_schema_report(frame: pd.DataFrame) -> Path:
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    report = pd.DataFrame(
        {
            "column": frame.columns,
            "dtype": frame.dtypes.astype(str).values,
            "non_null_count": frame.notna().sum().values,
            "null_count": frame.isna().sum().values,
            "null_pct": (frame.isna().mean().values * 100).round(4),
            "nunique": [frame[col].nunique(dropna=True) for col in frame.columns],
        }
    )
    output = TABLE_DIR / "schema_report.csv"
    report.to_csv(output, index=False)
    logger.info("Wrote schema report to %s", output)
    return output
