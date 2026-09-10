"""Layer 1: portfolio composition and volume analytics."""

from __future__ import annotations

import logging

import pandas as pd

from src.config import TARGET_COLUMN

logger = logging.getLogger(__name__)


def portfolio_kpis(frame: pd.DataFrame) -> dict:
    matured = frame.loc[frame["is_matured"] == True]  # noqa: E712
    defaults = matured.loc[matured[TARGET_COLUMN] == 1]
    charged_off = frame.loc[frame["is_charged_off"] == 1]
    return {
        "loan_count": int(len(frame)),
        "matured_loan_count": int(len(matured)),
        "funded_amount": float(frame["funded_amnt"].sum()),
        "requested_amount": float(frame["loan_amnt"].sum()),
        "average_loan_amount": float(frame["loan_amnt"].mean()),
        "median_loan_amount": float(frame["loan_amnt"].median()),
        "average_interest_rate": float(frame["int_rate"].mean()),
        "average_annual_income": float(frame["annual_inc"].mean()),
        "default_count": int(len(defaults)),
        "default_rate": float(defaults.shape[0] / matured.shape[0]) if len(matured) else None,
        "charged_off_count": int(len(charged_off)),
        "charged_off_rate": float(len(charged_off) / len(frame)) if len(frame) else None,
        "open_or_late_count": int((frame["performance_group"] == "open_or_late").sum()),
    }


def volume_by_year(frame: pd.DataFrame) -> pd.DataFrame:
    grouped = (
        frame.groupby("issue_year", dropna=False)
        .agg(
            loan_count=("id", "count"),
            funded_amount=("funded_amnt", "sum"),
            average_loan_amount=("loan_amnt", "mean"),
            average_interest_rate=("int_rate", "mean"),
        )
        .reset_index()
    )
    return grouped.sort_values("issue_year")


def composition_table(frame: pd.DataFrame, column: str) -> pd.DataFrame:
    table = (
        frame.groupby(column, dropna=False)
        .agg(
            loan_count=("id", "count"),
            funded_amount=("funded_amnt", "sum"),
            average_loan_amount=("loan_amnt", "mean"),
            average_interest_rate=("int_rate", "mean"),
        )
        .reset_index()
    )
    table["loan_share"] = table["loan_count"] / table["loan_count"].sum()
    table["funded_share"] = table["funded_amount"] / table["funded_amount"].sum()
    return table.sort_values("funded_amount", ascending=False)


def write_portfolio_tables(frame: pd.DataFrame, output_dir) -> dict[str, object]:
    kpis = portfolio_kpis(frame)
    tables = {
        "portfolio_kpis": pd.DataFrame([kpis]),
        "volume_by_year": volume_by_year(frame),
        "composition_by_grade": composition_table(frame, "grade"),
        "composition_by_purpose": composition_table(frame, "purpose"),
        "composition_by_term": composition_table(frame, "term_months"),
        "composition_by_home_ownership": composition_table(frame, "home_ownership"),
    }
    for name, table in tables.items():
        path = output_dir / f"{name}.csv"
        table.to_csv(path, index=False)
        logger.info("Wrote %s", path)
    return {"kpis": kpis, "tables": tables}
