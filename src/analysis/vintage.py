"""Layer 3: vintage and loan-age performance analysis."""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd

from src.config import TARGET_COLUMN, VINTAGE_MAX_AGE

logger = logging.getLogger(__name__)


def vintage_summary(frame: pd.DataFrame) -> pd.DataFrame:
    matured = frame.loc[frame["is_matured"] == True].copy()  # noqa: E712
    table = (
        matured.groupby("vintage", dropna=False)
        .agg(
            matured_loans=("id", "count"),
            default_count=(TARGET_COLUMN, "sum"),
            default_rate=(TARGET_COLUMN, "mean"),
            funded_amount=("funded_amnt", "sum"),
            average_interest_rate=("int_rate", "mean"),
            average_dti=("dti", "mean"),
        )
        .reset_index()
    )
    issued = (
        frame.groupby("vintage", dropna=False)
        .agg(issued_loans=("id", "count"), issued_funded=("funded_amnt", "sum"))
        .reset_index()
    )
    return issued.merge(table, on="vintage", how="left").sort_values("vintage")


def cumulative_vintage_curve(frame: pd.DataFrame, max_age: int = VINTAGE_MAX_AGE) -> pd.DataFrame:
    from src.config import SNAPSHOT_DATE
    from src.data.transform import month_diff

    work = frame.loc[frame["issue_d_dt"].notna() & frame["vintage"].notna()].copy()
    snapshot = pd.Timestamp(SNAPSHOT_DATE)
    work["observed_age"] = month_diff(work["issue_d_dt"], pd.Series(snapshot, index=work.index))
    work["default_age"] = np.where(work[TARGET_COLUMN] == 1, work["loan_age_months"], np.nan)
    if "recoveries" in work.columns:
        work["net_loss"] = np.where(
            work[TARGET_COLUMN] == 1,
            np.maximum(work["funded_amnt"] - work["recoveries"].fillna(0), 0),
            0,
        )
    else:
        work["net_loss"] = np.where(work[TARGET_COLUMN] == 1, work["funded_amnt"], 0)

    rows = []
    for vintage, part in work.groupby("vintage"):
        for age in range(0, max_age + 1):
            reached = part.loc[part["observed_age"] >= age]
            n = len(reached)
            if n == 0:
                continue
            defaults_by_age = int(((reached[TARGET_COLUMN] == 1) & (reached["default_age"] <= age)).sum())
            loss_by_age = float(
                reached.loc[(reached[TARGET_COLUMN] == 1) & (reached["default_age"] <= age), "net_loss"].sum()
            )
            funded = float(reached["funded_amnt"].sum())
            rows.append(
                {
                    "vintage": int(vintage) if not pd.isna(vintage) else vintage,
                    "loan_age_months": age,
                    "loans_reached_age": n,
                    "cumulative_defaults": defaults_by_age,
                    "cumulative_default_rate": defaults_by_age / n,
                    "cumulative_loss": loss_by_age,
                    "cumulative_loss_rate": loss_by_age / funded if funded else np.nan,
                }
            )
    return pd.DataFrame(rows)


def vintage_heatmap(curve: pd.DataFrame) -> pd.DataFrame:
    if curve.empty:
        return curve
    return curve.pivot(index="vintage", columns="loan_age_months", values="cumulative_default_rate")


def write_vintage_tables(frame: pd.DataFrame, output_dir) -> dict[str, pd.DataFrame]:
    summary = vintage_summary(frame)
    curve = cumulative_vintage_curve(frame)
    heatmap = vintage_heatmap(curve)
    summary.to_csv(output_dir / "vintage_summary.csv", index=False)
    curve.to_csv(output_dir / "vintage_curve.csv", index=False)
    heatmap.to_csv(output_dir / "vintage_heatmap.csv")
    logger.info("Wrote vintage tables")
    return {"summary": summary, "curve": curve, "heatmap": heatmap}
