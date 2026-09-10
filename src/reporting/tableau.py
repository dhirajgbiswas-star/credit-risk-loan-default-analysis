"""Build Tableau-ready extracts from analytical outputs."""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from src.config import MODEL_DIR, TABLE_DIR, TABLEAU_DIR

logger = logging.getLogger(__name__)


def _read(name: str) -> pd.DataFrame:
    path = TABLE_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"Required analytical table is missing: {path}")
    return pd.read_csv(path)


def build_tableau_extracts() -> dict[str, Path]:
    TABLEAU_DIR.mkdir(parents=True, exist_ok=True)
    written: dict[str, Path] = {}

    portfolio = _read("portfolio_kpis.csv")
    volume = _read("volume_by_year.csv")
    grade = _read("risk_by_grade.csv")
    purpose = _read("risk_by_purpose.csv")
    state = _read("risk_by_state.csv")
    vintage = _read("vintage_curve.csv")
    el_grade = _read("el_by_grade.csv")
    el_purpose = _read("el_by_purpose.csv")
    el_state = _read("el_by_state.csv")
    el_vintage = _read("el_by_vintage.csv")
    sensitivity = _read("el_sensitivity.csv")
    recommendations = _read("recommendation_matrix.csv") if (TABLE_DIR / "recommendation_matrix.csv").exists() else pd.DataFrame()

    portfolio_summary = portfolio.copy()
    if not volume.empty:
        portfolio_summary["latest_issue_year"] = volume["issue_year"].max()
    path = TABLEAU_DIR / "tableau_portfolio_summary.csv"
    portfolio_summary.to_csv(path, index=False)
    written["portfolio_summary"] = path

    grade.to_csv(TABLEAU_DIR / "tableau_risk_by_grade.csv", index=False)
    purpose.to_csv(TABLEAU_DIR / "tableau_risk_by_purpose.csv", index=False)
    state.to_csv(TABLEAU_DIR / "tableau_risk_by_state.csv", index=False)
    vintage.to_csv(TABLEAU_DIR / "tableau_vintage.csv", index=False)

    el = pd.concat(
        [
            el_grade.assign(segment_type="grade", segment=el_grade["grade"].astype(str)),
            el_purpose.assign(segment_type="purpose", segment=el_purpose["purpose"].astype(str)),
            el_state.assign(segment_type="state", segment=el_state["addr_state"].astype(str)),
            el_vintage.assign(segment_type="vintage", segment=el_vintage["vintage"].astype(str)),
        ],
        ignore_index=True,
        sort=False,
    )
    el.to_csv(TABLEAU_DIR / "tableau_expected_loss.csv", index=False)

    pred_path = MODEL_DIR / "test_predictions.parquet"
    if pred_path.exists():
        preds = pd.read_parquet(pred_path)
        keep = [c for c in ["grade", "purpose", "term_months", "predicted_pd", "actual_default", "risk_band", "loan_amnt", "int_rate", "dti", "annual_inc"] if c in preds.columns]
        preds[keep].to_csv(TABLEAU_DIR / "tableau_model_predictions.csv", index=False)
    else:
        logger.warning("Model predictions are not available yet.")

    if not recommendations.empty:
        recommendations.to_csv(TABLEAU_DIR / "tableau_recommendations.csv", index=False)

    kpi = portfolio.copy()
    if not sensitivity.empty:
        base = sensitivity.loc[sensitivity["scenario"] == "Base"].iloc[0]
        kpi["expected_loss"] = base["expected_loss"]
        kpi["expected_loss_pct"] = base["expected_loss_pct"]
        kpi["lgd_assumption"] = base["lgd_assumption"]
        kpi["average_pd"] = base["pd"]
    kpi.to_csv(TABLEAU_DIR / "tableau_kpi_summary.csv", index=False)

    volume.to_csv(TABLEAU_DIR / "tableau_volume_by_year.csv", index=False)
    sensitivity.to_csv(TABLEAU_DIR / "tableau_el_sensitivity.csv", index=False)

    logger.info("Wrote Tableau extracts to %s", TABLEAU_DIR)
    return written
