"""Feature engineering and analytical buckets used across risk and modelling work."""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd

from src.config import SNAPSHOT_DATE

logger = logging.getLogger(__name__)


def month_diff(start: pd.Series, end: pd.Series) -> pd.Series:
    return (end.dt.year - start.dt.year) * 12 + (end.dt.month - start.dt.month)


def add_vintage_fields(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    if "issue_d_dt" not in out.columns:
        raise KeyError("issue_d_dt is required. Run clean_accepted_loans first.")

    out["issue_year"] = out["issue_d_dt"].dt.year
    out["issue_quarter"] = out["issue_d_dt"].dt.to_period("Q").astype(str)
    out["issue_month"] = out["issue_d_dt"].dt.strftime("%Y-%m")
    out["vintage"] = out["issue_year"]

    snapshot = pd.Timestamp(SNAPSHOT_DATE)
    observation_end = out["last_pymnt_d_dt"] if "last_pymnt_d_dt" in out.columns else pd.Series(snapshot, index=out.index)
    observation_end = observation_end.fillna(snapshot)
    observation_end = observation_end.clip(upper=snapshot)
    out["loan_age_months"] = month_diff(out["issue_d_dt"], observation_end)
    out["loan_age_months"] = out["loan_age_months"].clip(lower=0)
    return out


def add_risk_features(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    out["annual_inc"] = out["annual_inc"].clip(lower=0)
    out["loan_to_income"] = np.where(
        out["annual_inc"] > 0, out["loan_amnt"] / out["annual_inc"], np.nan
    )
    monthly_income = out["annual_inc"] / 12.0
    out["installment_to_income"] = np.where(
        monthly_income > 0, out["installment"] / monthly_income, np.nan
    )
    if {"earliest_cr_line_dt", "issue_d_dt"}.issubset(out.columns):
        out["credit_history_years"] = month_diff(out["earliest_cr_line_dt"], out["issue_d_dt"]) / 12.0
        out["credit_history_years"] = out["credit_history_years"].clip(lower=0)

    out["annual_income_log"] = np.log1p(out["annual_inc"])
    out["loan_amount_log"] = np.log1p(out["loan_amnt"])

    out["income_bucket"] = pd.cut(
        out["annual_inc"],
        bins=[-np.inf, 40000, 60000, 85000, 125000, np.inf],
        labels=["<=40k", "40-60k", "60-85k", "85-125k", ">125k"],
    )
    out["dti_bucket"] = pd.cut(
        out["dti"],
        bins=[-np.inf, 10, 15, 20, 25, 30, np.inf],
        labels=["<=10", "10-15", "15-20", "20-25", "25-30", ">30"],
    )
    out["loan_amount_bucket"] = pd.cut(
        out["loan_amnt"],
        bins=[-np.inf, 5000, 10000, 15000, 25000, np.inf],
        labels=["<=5k", "5-10k", "10-15k", "15-25k", ">25k"],
    )
    if "int_rate" in out.columns:
        out["interest_rate_bucket"] = pd.cut(
            out["int_rate"],
            bins=[-np.inf, 8, 12, 16, 20, np.inf],
            labels=["<=8%", "8-12%", "12-16%", "16-20%", ">20%"],
        )
    if "emp_length_years" in out.columns:
        out["employment_length_bucket"] = pd.cut(
            out["emp_length_years"],
            bins=[-np.inf, 0, 2, 5, 9, np.inf],
            labels=["<1 year", "1-2 years", "3-5 years", "6-9 years", "10+ years"],
        )
    if "revol_util" in out.columns:
        out["revolving_utilisation_bucket"] = pd.cut(
            out["revol_util"],
            bins=[-np.inf, 20, 40, 60, 80, np.inf],
            labels=["<=20%", "20-40%", "40-60%", "60-80%", ">80%"],
        )
    return out


def assign_observed_risk_segment(frame: pd.DataFrame, default_rate_by_grade: pd.Series) -> pd.DataFrame:
    """Assign Low/Medium/High/Very High using grade-level observed default rates."""
    out = frame.copy()
    mapped = out["grade"].map(default_rate_by_grade)
    thresholds = mapped.quantile([0.25, 0.50, 0.75]).tolist()
    out["observed_risk_segment"] = pd.cut(
        mapped,
        bins=[-np.inf, thresholds[0], thresholds[1], thresholds[2], np.inf],
        labels=["Low Risk", "Medium Risk", "High Risk", "Very High Risk"],
    )
    return out


def build_analytical_dataset(frame: pd.DataFrame) -> pd.DataFrame:
    from src.data.clean import assign_target, clean_accepted_loans

    cleaned = clean_accepted_loans(frame)
    cleaned = assign_target(cleaned)
    cleaned = add_vintage_fields(cleaned)
    cleaned = add_risk_features(cleaned)
    logger.info("Analytical dataset ready: %s rows", f"{len(cleaned):,}")
    return cleaned
