"""Layer 4: transparent expected-loss framework. EL = PD x LGD x EAD."""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd

from src.config import LGD_ADVERSE, LGD_BASE, LGD_OPTIMISTIC, TARGET_COLUMN

logger = logging.getLogger(__name__)


def calculate_expected_loss(pd: float, lgd: float, ead: float) -> float:
    return float(pd) * float(lgd) * float(ead)


def observed_recovery_rate(frame: pd.DataFrame) -> dict:
    defaults = frame.loc[frame[TARGET_COLUMN] == 1].copy()
    if defaults.empty or "recoveries" not in defaults.columns:
        return {
            "default_count": 0,
            "recovery_rate": np.nan,
            "implied_lgd": np.nan,
            "note": "Insufficient recovery information on defaulted loans.",
        }
    ead = defaults["funded_amnt"].replace(0, np.nan)
    recovery = defaults["recoveries"].fillna(0) / ead
    recovery = recovery.replace([np.inf, -np.inf], np.nan).dropna()
    recovery_rate = float(recovery.clip(lower=0, upper=1).mean()) if len(recovery) else np.nan
    return {
        "default_count": int(len(defaults)),
        "recovery_rate": recovery_rate,
        "implied_lgd": 1 - recovery_rate if pd.notna(recovery_rate) else np.nan,
        "note": (
            "Recovery rate is estimated as recoveries / funded_amnt on defaulted loans. "
            "This is an analytical estimate, not an official Lending Club LGD metric."
        ),
    }


def segment_expected_loss(
    frame: pd.DataFrame,
    column: str,
    lgd: float = LGD_BASE,
) -> pd.DataFrame:
    matured = frame.loc[frame["is_matured"] == True].copy()  # noqa: E712
    rows = []
    for key, part in matured.groupby(column, dropna=False):
        pd_rate = float(part[TARGET_COLUMN].mean()) if len(part) else np.nan
        ead = float(part["funded_amnt"].sum())
        el = calculate_expected_loss(pd_rate, lgd, ead) if pd.notna(pd_rate) else np.nan
        rows.append(
            {
                column: key,
                "loan_count": int(len(part)),
                "pd": pd_rate,
                "lgd_assumption": lgd,
                "ead": ead,
                "expected_loss": el,
                "expected_loss_pct": el / ead if ead else np.nan,
                "average_loan_amount": float(part["loan_amnt"].mean()) if len(part) else np.nan,
            }
        )
    table = pd.DataFrame(rows)
    if table.empty:
        return table
    return table.sort_values("expected_loss", ascending=False)


def portfolio_expected_loss(frame: pd.DataFrame, lgd: float = LGD_BASE) -> dict:
    matured = frame.loc[frame["is_matured"] == True]  # noqa: E712
    pd_rate = float(matured[TARGET_COLUMN].mean()) if len(matured) else np.nan
    ead = float(matured["funded_amnt"].sum()) if len(matured) else 0.0
    el = calculate_expected_loss(pd_rate, lgd, ead) if pd.notna(pd_rate) else np.nan
    return {
        "scenario": None,
        "lgd_assumption": lgd,
        "pd": pd_rate,
        "ead": ead,
        "expected_loss": el,
        "expected_loss_pct": el / ead if ead else np.nan,
        "matured_loans": int(len(matured)),
    }


def sensitivity_table(frame: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for name, lgd in (
        ("Optimistic", LGD_OPTIMISTIC),
        ("Base", LGD_BASE),
        ("Adverse", LGD_ADVERSE),
    ):
        result = portfolio_expected_loss(frame, lgd=lgd)
        result["scenario"] = name
        rows.append(result)
    return pd.DataFrame(rows)


def write_expected_loss_tables(frame: pd.DataFrame, output_dir) -> dict:
    recovery = observed_recovery_rate(frame)
    sensitivity = sensitivity_table(frame)
    tables = {
        "el_by_grade": segment_expected_loss(frame, "grade"),
        "el_by_purpose": segment_expected_loss(frame, "purpose"),
        "el_by_state": segment_expected_loss(frame, "addr_state"),
        "el_by_vintage": segment_expected_loss(frame, "vintage"),
        "el_by_term": segment_expected_loss(frame, "term_months"),
        "el_sensitivity": sensitivity,
        "recovery_estimate": pd.DataFrame([recovery]),
    }
    for name, table in tables.items():
        table.to_csv(output_dir / f"{name}.csv", index=False)
    logger.info("Wrote expected-loss tables. Observed recovery estimate: %s", recovery)
    return {"recovery": recovery, "sensitivity": sensitivity, "tables": tables}
