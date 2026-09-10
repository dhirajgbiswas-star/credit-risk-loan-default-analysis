"""Standardise types, categories and invalid records without silently dropping outliers."""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd

from src.config import DEFAULT_STATUSES, EXCLUDED_STATUSES, NON_DEFAULT_STATUSES, TARGET_COLUMN

logger = logging.getLogger(__name__)

EMP_LENGTH_MAP = {
    "< 1 year": 0,
    "1 year": 1,
    "2 years": 2,
    "3 years": 3,
    "4 years": 4,
    "5 years": 5,
    "6 years": 6,
    "7 years": 7,
    "8 years": 8,
    "9 years": 9,
    "10+ years": 10,
}


def parse_month_year(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series, format="%b-%Y", errors="coerce")


def clean_accepted_loans(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    if "id" in out.columns:
        out = out[out["id"].notna()].copy()
        out["id"] = out["id"].astype(str)
        out = out.drop_duplicates(subset=["id"], keep="first")

    if "loan_status" in out.columns:
        out["loan_status"] = out["loan_status"].astype(str).str.strip()
        out = out[out["loan_status"].ne("") & out["loan_status"].ne("nan")].copy()

    numeric_cols = [
        "loan_amnt",
        "funded_amnt",
        "funded_amnt_inv",
        "int_rate",
        "installment",
        "annual_inc",
        "dti",
        "delinq_2yrs",
        "fico_range_low",
        "fico_range_high",
        "inq_last_6mths",
        "open_acc",
        "pub_rec",
        "revol_bal",
        "revol_util",
        "total_acc",
        "pub_rec_bankruptcies",
        "mort_acc",
        "recoveries",
        "collection_recovery_fee",
        "total_pymnt",
        "out_prncp",
    ]
    for col in numeric_cols:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce")

    if "term" in out.columns:
        out["term_months"] = (
            out["term"].astype(str).str.extract(r"(\d+)", expand=False).astype(float)
        )

    if "emp_length" in out.columns:
        out["emp_length_years"] = out["emp_length"].map(EMP_LENGTH_MAP)

    for col in ("issue_d", "last_pymnt_d", "earliest_cr_line"):
        if col in out.columns:
            out[f"{col}_dt"] = parse_month_year(out[col])

    for col in ("grade", "sub_grade", "purpose", "home_ownership", "verification_status", "addr_state"):
        if col in out.columns:
            out[col] = out[col].astype(str).str.strip()
            out.loc[out[col].isin(["", "nan", "None"]), col] = np.nan

    if "home_ownership" in out.columns:
        out["home_ownership"] = out["home_ownership"].replace({"NONE": "OTHER", "ANY": "OTHER"})

    if "purpose" in out.columns:
        out["purpose"] = out["purpose"].str.lower()

    if {"funded_amnt", "loan_amnt"}.issubset(out.columns):
        invalid_funding = out["funded_amnt"] > out["loan_amnt"] + 1e-6
        if invalid_funding.any():
            logger.warning("Removing %s records where funded_amnt exceeds loan_amnt", int(invalid_funding.sum()))
            out = out.loc[~invalid_funding].copy()

    if "loan_amnt" in out.columns:
        out = out.loc[out["loan_amnt"].isna() | (out["loan_amnt"] > 0)].copy()

    logger.info("Cleaned dataset contains %s rows", f"{len(out):,}")
    return out


def assign_target(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    status = out["loan_status"]
    out["is_matured"] = status.isin(DEFAULT_STATUSES + NON_DEFAULT_STATUSES)
    out[TARGET_COLUMN] = np.where(
        status.isin(DEFAULT_STATUSES),
        1,
        np.where(status.isin(NON_DEFAULT_STATUSES), 0, np.nan),
    )
    out["is_charged_off"] = status.isin(
        ("Charged Off", "Does not meet the credit policy. Status:Charged Off")
    ).astype(int)
    out["performance_group"] = np.select(
        [
            status.isin(DEFAULT_STATUSES),
            status.isin(NON_DEFAULT_STATUSES),
            status.isin(EXCLUDED_STATUSES),
        ],
        ["default", "non_default", "open_or_late"],
        default="unclassified",
    )
    return out
