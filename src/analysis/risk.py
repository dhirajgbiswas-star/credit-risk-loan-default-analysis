"""Layer 2: credit-risk segmentation and concentration analysis."""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd
from scipy import stats

from src.config import MIN_SEGMENT_N, STATE_MIN_N, TARGET_COLUMN

logger = logging.getLogger(__name__)


def _wilson_interval(successes: int, n: int, alpha: float = 0.05) -> tuple[float, float]:
    if n == 0:
        return (np.nan, np.nan)
    z = stats.norm.ppf(1 - alpha / 2)
    phat = successes / n
    denom = 1 + z**2 / n
    centre = (phat + z**2 / (2 * n)) / denom
    spread = (z * np.sqrt((phat * (1 - phat) + z**2 / (4 * n)) / n)) / denom
    return (max(0.0, centre - spread), min(1.0, centre + spread))


def risk_by_segment(
    frame: pd.DataFrame,
    column: str,
    min_n: int = MIN_SEGMENT_N,
) -> pd.DataFrame:
    matured = frame.loc[frame["is_matured"] == True].copy()  # noqa: E712
    grouped = matured.groupby(column, dropna=False)
    rows = []
    for key, part in grouped:
        n = len(part)
        defaults = int(part[TARGET_COLUMN].sum())
        low, high = _wilson_interval(defaults, n)
        rows.append(
            {
                column: key,
                "loan_count": n,
                "default_count": defaults,
                "default_rate": defaults / n if n else np.nan,
                "default_rate_ci_low": low,
                "default_rate_ci_high": high,
                "charged_off_rate": part["is_charged_off"].mean() if n else np.nan,
                "funded_amount": part["funded_amnt"].sum(),
                "average_loan_amount": part["loan_amnt"].mean(),
                "average_interest_rate": part["int_rate"].mean(),
                "average_dti": part["dti"].mean() if "dti" in part.columns else np.nan,
                "meets_sample_threshold": n >= min_n,
            }
        )
    table = pd.DataFrame(rows)
    if table.empty:
        return table
    return table.sort_values("default_rate", ascending=False)


def risk_concentration(frame: pd.DataFrame, column: str) -> pd.DataFrame:
    table = risk_by_segment(frame, column)
    if table.empty:
        return table
    table["exposure_share"] = table["funded_amount"] / table["funded_amount"].sum()
    table["default_share"] = table["default_count"] / table["default_count"].sum()
    median_rate = table.loc[table["meets_sample_threshold"], "default_rate"].median()
    median_exposure = table.loc[table["meets_sample_threshold"], "funded_amount"].median()
    table["high_risk"] = table["default_rate"] >= median_rate
    table["high_exposure"] = table["funded_amount"] >= median_exposure
    table["concentration_quadrant"] = np.select(
        [
            table["high_risk"] & table["high_exposure"],
            table["high_risk"] & ~table["high_exposure"],
            ~table["high_risk"] & table["high_exposure"],
        ],
        ["Prioritise", "Investigate", "Optimise"],
        default="Monitor",
    )
    return table


def write_risk_tables(frame: pd.DataFrame, output_dir) -> dict[str, pd.DataFrame]:
    tables = {
        "risk_by_grade": risk_by_segment(frame, "grade", min_n=1),
        "risk_by_purpose": risk_by_segment(frame, "purpose"),
        "risk_by_term": risk_by_segment(frame, "term_months", min_n=1),
        "risk_by_income_bucket": risk_by_segment(frame, "income_bucket", min_n=1),
        "risk_by_dti_bucket": risk_by_segment(frame, "dti_bucket", min_n=1),
        "risk_by_interest_rate_bucket": risk_by_segment(frame, "interest_rate_bucket", min_n=1),
        "risk_by_employment_length": risk_by_segment(frame, "employment_length_bucket", min_n=1),
        "risk_by_loan_amount_bucket": risk_by_segment(frame, "loan_amount_bucket", min_n=1),
        "risk_by_home_ownership": risk_by_segment(frame, "home_ownership", min_n=1),
        "risk_by_state": risk_by_segment(frame, "addr_state", min_n=STATE_MIN_N),
        "concentration_by_grade": risk_concentration(frame, "grade"),
        "concentration_by_purpose": risk_concentration(frame, "purpose"),
    }
    for name, table in tables.items():
        table.to_csv(output_dir / f"{name}.csv", index=False)
        logger.info("Wrote %s", name)
    return tables
