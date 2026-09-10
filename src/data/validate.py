"""Data quality checks for completeness, validity, uniqueness and integrity."""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from src.config import TABLE_DIR

logger = logging.getLogger(__name__)


def _row(check: str, dimension: str, status: str, value, detail: str) -> dict:
    return {
        "check": check,
        "dimension": dimension,
        "status": status,
        "value": value,
        "detail": detail,
    }


def run_quality_checks(frame: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict] = []
    n = len(frame)

    missing = frame.isna().mean().sort_values(ascending=False)
    high_missing = missing[missing > 0.20]
    rows.append(
        _row(
            "row_count",
            "completeness",
            "pass" if n > 0 else "fail",
            n,
            "Total loaded records",
        )
    )
    rows.append(
        _row(
            "columns_with_over_20pct_missing",
            "completeness",
            "warn" if len(high_missing) else "pass",
            int(len(high_missing)),
            ", ".join(high_missing.index[:15]) if len(high_missing) else "None",
        )
    )

    if "id" in frame.columns:
        dup_id = int(frame["id"].duplicated().sum())
        rows.append(
            _row(
                "duplicate_loan_ids",
                "uniqueness",
                "fail" if dup_id else "pass",
                dup_id,
                "Duplicate values in id",
            )
        )
    full_dups = int(frame.duplicated().sum())
    rows.append(
        _row(
            "duplicate_rows",
            "uniqueness",
            "fail" if full_dups else "pass",
            full_dups,
            "Exact duplicate records",
        )
    )

    if "int_rate" in frame.columns:
        invalid_rate = int(((frame["int_rate"] < 0) | (frame["int_rate"] > 40)).sum())
        rows.append(
            _row(
                "invalid_interest_rate",
                "validity",
                "fail" if invalid_rate else "pass",
                invalid_rate,
                "Interest rate outside 0-40",
            )
        )
    if "dti" in frame.columns:
        invalid_dti = int(((frame["dti"] < 0) | (frame["dti"] > 100)).sum())
        rows.append(
            _row(
                "extreme_dti",
                "validity",
                "warn" if invalid_dti else "pass",
                invalid_dti,
                "DTI below 0 or above 100. Extreme values are retained pending review.",
            )
        )
    if "loan_amnt" in frame.columns:
        negative_loan = int((frame["loan_amnt"] <= 0).sum())
        rows.append(
            _row(
                "non_positive_loan_amount",
                "validity",
                "fail" if negative_loan else "pass",
                negative_loan,
                "loan_amnt must be positive",
            )
        )
    if "annual_inc" in frame.columns:
        negative_inc = int((frame["annual_inc"] < 0).sum())
        rows.append(
            _row(
                "negative_annual_income",
                "validity",
                "fail" if negative_inc else "pass",
                negative_inc,
                "annual_inc must be non-negative",
            )
        )
    if "term" in frame.columns:
        term_values = (
            frame["term"].astype(str).str.extract(r"(\d+)", expand=False).dropna().unique()
        )
        unexpected = [v for v in term_values if v not in {"36", "60"}]
        rows.append(
            _row(
                "unexpected_loan_term",
                "validity",
                "fail" if unexpected else "pass",
                len(unexpected),
                f"Unexpected terms: {unexpected}" if unexpected else "Only 36 and 60 month terms",
            )
        )

    if {"funded_amnt", "loan_amnt"}.issubset(frame.columns):
        overfunded = int((frame["funded_amnt"] > frame["loan_amnt"] + 1e-6).sum())
        rows.append(
            _row(
                "funded_exceeds_requested",
                "integrity",
                "fail" if overfunded else "pass",
                overfunded,
                "funded_amnt should not exceed loan_amnt",
            )
        )
    if "loan_status" in frame.columns:
        blank_status = int(frame["loan_status"].isna().sum() + (frame["loan_status"].astype(str).str.strip() == "").sum())
        rows.append(
            _row(
                "blank_loan_status",
                "consistency",
                "warn" if blank_status else "pass",
                blank_status,
                "Records with missing loan_status are excluded from target construction",
            )
        )

    report = pd.DataFrame(rows)
    logger.info("Completed %s data quality checks", len(report))
    return report


def write_quality_report(report: pd.DataFrame) -> Path:
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    csv_path = TABLE_DIR / "data_quality_report.csv"
    report.to_csv(csv_path, index=False)

    html_path = TABLE_DIR / "data_quality_report.html"
    html_path.write_text(report.to_html(index=False), encoding="utf-8")
    logger.info("Wrote quality reports to %s and %s", csv_path, html_path)
    return csv_path
