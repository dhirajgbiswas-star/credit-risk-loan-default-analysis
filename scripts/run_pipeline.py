#!/usr/bin/env python3
"""Build the analytical dataset and run portfolio, risk, vintage and expected-loss analysis."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.analysis.expected_loss import write_expected_loss_tables
from src.analysis.portfolio import write_portfolio_tables
from src.analysis.risk import write_risk_tables
from src.analysis.vintage import write_vintage_tables
from src.config import FIGURE_DIR, PROCESSED_DIR, TABLE_DIR, configure_logging, ensure_directories
from src.data.load import load_accepted_loans, write_schema_report
from src.data.transform import build_analytical_dataset
from src.data.validate import run_quality_checks, write_quality_report
from src.reporting.plots import bar_rate, distribution, trend_dual, vintage_heatmap_plot, vintage_lines


def main() -> None:
    configure_logging()
    ensure_directories()

    raw = load_accepted_loans()
    write_schema_report(raw)
    write_quality_report(run_quality_checks(raw))

    analytical = build_analytical_dataset(raw)
    analytical_path = PROCESSED_DIR / "analytical_loans.parquet"
    analytical.to_parquet(analytical_path, index=False)

    portfolio = write_portfolio_tables(analytical, TABLE_DIR)
    risk_tables = write_risk_tables(analytical, TABLE_DIR)
    vintage_tables = write_vintage_tables(analytical, TABLE_DIR)
    el = write_expected_loss_tables(analytical, TABLE_DIR)

    distribution(analytical["loan_amnt"], "Loan amount distribution", "loan_amount_distribution.png")
    distribution(analytical["int_rate"], "Interest rate distribution", "interest_rate_distribution.png")
    trend_dual(
        portfolio["tables"]["volume_by_year"],
        "issue_year",
        "loan_count",
        "funded_amount",
        "Loan volume and funded amount by issue year",
        "portfolio_trend.png",
    )
    bar_rate(risk_tables["risk_by_grade"], "grade", "Default rate by grade", "default_rate_by_grade.png")
    bar_rate(risk_tables["risk_by_purpose"], "purpose", "Default rate by purpose", "default_rate_by_purpose.png")
    bar_rate(risk_tables["risk_by_term"], "term_months", "Default rate by term", "default_rate_by_term.png")
    bar_rate(risk_tables["risk_by_income_bucket"], "income_bucket", "Default rate by income", "default_rate_by_income.png")
    bar_rate(risk_tables["risk_by_dti_bucket"], "dti_bucket", "Default rate by DTI", "default_rate_by_dti.png")
    if not vintage_tables["curve"].empty:
        vintage_lines(vintage_tables["curve"])
        vintage_heatmap_plot(vintage_tables["heatmap"])

    summary = {
        "kpis": portfolio["kpis"],
        "recovery": el["recovery"],
        "analytical_rows": int(len(analytical)),
        "outputs": {
            "analytical_dataset": str(analytical_path),
            "tables": str(TABLE_DIR),
            "figures": str(FIGURE_DIR),
        },
    }
    (TABLE_DIR / "pipeline_summary.json").write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    print(json.dumps(summary["kpis"], indent=2))


if __name__ == "__main__":
    main()
