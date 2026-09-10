"""Render README preview images that match the six Tableau dashboards."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.gridspec import GridSpec
from matplotlib.patches import FancyBboxPatch

from src.config import FIGURE_DIR, TABLE_DIR, TABLEAU_DIR

NAVY = "#1B365D"
NAVY_MID = "#2F5D8A"
INK = "#1C2430"
MUTED = "#5B6B7C"
CANVAS = "#E8EDF3"
CARD = "#FFFFFF"
RISK = "#8C2F3B"
LINE = "#D4DCE6"

INSIGHTS = {
    "executive": "Grade D combines a 30.4% default rate with $3.07B exposure and should be prioritised.",
    "segmentation": "60-month loans default at 32.5% versus 16.0% for 36-month loans.",
    "vintage": "Default risk emerges between loan ages 12 and 36 months. 2016 is the weakest large vintage at 23.3%.",
    "expected_loss": "Grade C contributes the largest expected-loss dollars ($608M base case).",
    "model": "The model ranks risk well (3.5% to 46.9% across PD deciles) but overstates absolute probabilities.",
    "decisions": "P1 actions target grade D, grade C expected-loss dollars, and term/purpose pricing.",
}


def _read(name: str) -> pd.DataFrame:
    for folder in (TABLEAU_DIR, TABLE_DIR):
        path = folder / name
        if path.exists():
            return pd.read_csv(path)
    raise FileNotFoundError(name)


def _money(value: float) -> str:
    if abs(value) >= 1_000_000_000:
        return f"${value / 1_000_000_000:,.2f}B"
    if abs(value) >= 1_000_000:
        return f"${value / 1_000_000:,.1f}M"
    return f"${value:,.0f}"


def _count(value: float) -> str:
    if abs(value) >= 1_000_000:
        return f"{value / 1_000_000:,.2f}M"
    return f"{value:,.0f}"


def _style_ax(ax, title: str) -> None:
    ax.set_facecolor(CARD)
    ax.set_title(title, loc="left", fontsize=10, color=NAVY, fontweight="bold", pad=8)
    ax.tick_params(colors=MUTED, labelsize=8)
    for spine in ax.spines.values():
        spine.set_color(LINE)
    ax.yaxis.grid(True, color="#EDF1F6", linewidth=0.8)
    ax.set_axisbelow(True)


def _header(fig, title: str, subtitle: str) -> None:
    fig.patch.set_facecolor(CANVAS)
    banner = fig.add_axes([0.02, 0.925, 0.96, 0.055])
    banner.set_xlim(0, 1)
    banner.set_ylim(0, 1)
    banner.axis("off")
    banner.add_patch(FancyBboxPatch((0, 0), 1, 1, boxstyle="square,pad=0", facecolor=NAVY, edgecolor="none"))
    banner.text(0.012, 0.62, title, color="white", fontsize=13, fontweight="bold", va="center")
    banner.text(0.012, 0.28, subtitle, color="#D7DEE8", fontsize=8.5, va="center")


def _insight(fig, key: str, y: float = 0.868) -> None:
    box = fig.add_axes([0.02, y, 0.96, 0.048])
    box.set_xlim(0, 1)
    box.set_ylim(0, 1)
    box.axis("off")
    box.add_patch(FancyBboxPatch((0, 0), 1, 1, boxstyle="square,pad=0", facecolor=CARD, edgecolor=LINE, linewidth=0.8))
    box.add_patch(FancyBboxPatch((0, 0), 0.008, 1, boxstyle="square,pad=0", facecolor=NAVY_MID, edgecolor="none"))
    box.text(0.02, 0.5, f"KEY INSIGHT  {INSIGHTS[key]}", color=INK, fontsize=8.5, va="center")


def _kpis(fig, items: list[tuple[str, str, str]]) -> None:
    n = len(items)
    width = 0.96 / n
    for i, (label, value, accent) in enumerate(items):
        ax = fig.add_axes([0.02 + i * width, 0.80, width - 0.008, 0.06])
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis("off")
        ax.add_patch(FancyBboxPatch((0, 0), 1, 1, boxstyle="square,pad=0", facecolor=CARD, edgecolor=LINE, linewidth=0.8))
        ax.add_patch(FancyBboxPatch((0, 0), 0.03, 1, boxstyle="square,pad=0", facecolor=accent, edgecolor="none"))
        ax.text(0.08, 0.68, label, color=MUTED, fontsize=6.5, va="center")
        ax.text(0.08, 0.32, value, color=NAVY, fontsize=11, fontweight="bold", va="center")


def _footer(fig) -> None:
    ax = fig.add_axes([0.02, 0.012, 0.96, 0.022])
    ax.axis("off")
    ax.text(
        0,
        0.5,
        "Lending Club accepted loans, 2007–2018  ·  Matured outcomes  ·  Base-case LGD 50%",
        color=MUTED,
        fontsize=7.5,
        va="center",
    )


def _save(fig, name: str) -> Path:
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    path = FIGURE_DIR / name
    fig.savefig(path, dpi=150, facecolor=fig.get_facecolor())
    plt.close(fig)
    return path


def dashboard_01() -> Path:
    kpi = _read("tableau_kpi_summary.csv").iloc[0]
    volume = _read("tableau_volume_by_year.csv").dropna(subset=["issue_year"])
    vintage = _read("tableau_vintage_summary.csv").dropna(subset=["vintage"])
    el = _read("tableau_el_by_grade.csv").sort_values("grade")
    conc = _read("tableau_concentration_by_grade.csv")
    purpose = _read("tableau_el_by_purpose.csv").nlargest(8, "expected_loss")

    fig = plt.figure(figsize=(16, 10.2))
    _header(
        fig,
        "Credit Risk & Loan Default Analysis  ·  Executive Risk Overview",
        "Book size, matured default rate, and where expected loss is concentrated",
    )
    _kpis(
        fig,
        [
            ("FUNDED AMOUNT", _money(float(kpi["funded_amount"])), NAVY),
            ("LOAN COUNT", _count(float(kpi["loan_count"])), NAVY),
            ("DEFAULT RATE", f"{100 * kpi['default_rate']:.1f}%", RISK),
            ("CHARGED-OFF RATE", f"{100 * kpi['charged_off_rate']:.1f}%", RISK),
            ("EXPECTED LOSS $", _money(float(kpi["expected_loss"])), RISK),
            ("EXPECTED LOSS %", f"{100 * kpi['expected_loss_pct']:.1f}%", RISK),
            ("AVERAGE PD", f"{100 * kpi['average_pd']:.1f}%", NAVY_MID),
        ],
    )
    _insight(fig, "executive")
    gs = GridSpec(2, 3, left=0.05, right=0.98, top=0.78, bottom=0.06, wspace=0.28, hspace=0.38, figure=fig)

    ax = fig.add_subplot(gs[0, 0])
    ax.bar(volume["issue_year"].astype(int).astype(str), volume["loan_count"] / 1e6, color=NAVY_MID)
    _style_ax(ax, "Loan count by issue year (millions)")
    ax.set_ylabel("Loans (m)")

    ax = fig.add_subplot(gs[0, 1])
    ax.bar(volume["issue_year"].astype(int).astype(str), volume["funded_amount"] / 1e9, color=NAVY)
    _style_ax(ax, "Funded amount by issue year ($B)")
    ax.set_ylabel("$B")

    ax = fig.add_subplot(gs[0, 2])
    vint = vintage.sort_values("vintage")
    ax.bar(vint["vintage"].astype(int).astype(str), vint["default_rate"] * 100, color=RISK)
    _style_ax(ax, "Matured default rate by vintage")
    ax.set_ylabel("%")

    ax = fig.add_subplot(gs[1, 0])
    ax.bar(el["grade"], el["expected_loss"] / 1e6, color=NAVY)
    _style_ax(ax, "Expected loss by grade ($M)")
    ax.set_ylabel("$M")

    ax = fig.add_subplot(gs[1, 1])
    ax.scatter(conc["funded_amount"] / 1e9, conc["default_rate"] * 100, s=90, c=NAVY_MID, zorder=3)
    for _, row in conc.iterrows():
        ax.annotate(str(row["grade"]), (row["funded_amount"] / 1e9, row["default_rate"] * 100), color=INK, fontsize=8, xytext=(4, 4), textcoords="offset points")
    _style_ax(ax, "Default rate vs funded exposure")
    ax.set_xlabel("Funded ($B)")
    ax.set_ylabel("Default rate (%)")

    ax = fig.add_subplot(gs[1, 2])
    labels = purpose["purpose"].str.replace("_", " ")
    ax.barh(labels[::-1], purpose["expected_loss"][::-1] / 1e6, color=NAVY_MID)
    _style_ax(ax, "Expected loss by purpose ($M)")
    ax.set_xlabel("$M")

    _footer(fig)
    return _save(fig, "dashboard_01_executive_risk_overview.png")


def dashboard_02() -> Path:
    grade = _read("tableau_risk_by_grade.csv").sort_values("grade")
    purpose = _read("tableau_risk_by_purpose.csv").sort_values("default_rate", ascending=False).head(8)
    term = _read("tableau_risk_by_term.csv")
    income = _read("tableau_risk_by_income_bucket.csv")
    dti = _read("tableau_risk_by_dti_bucket.csv")
    el = _read("tableau_el_by_grade.csv").sort_values("grade")

    fig = plt.figure(figsize=(16, 10.2))
    _header(
        fig,
        "Credit Risk & Loan Default Analysis  ·  Credit Risk Segmentation",
        "Which grades, purposes, terms, incomes and DTI bands drive observed default",
    )
    _insight(fig, "segmentation", y=0.86)
    gs = GridSpec(2, 3, left=0.06, right=0.98, top=0.84, bottom=0.06, wspace=0.32, hspace=0.38, figure=fig)

    ax = fig.add_subplot(gs[0, 0])
    ax.bar(grade["grade"], grade["default_rate"] * 100, color=RISK)
    _style_ax(ax, "Default rate by grade")
    ax.set_ylabel("%")

    ax = fig.add_subplot(gs[0, 1])
    ax.barh(purpose["purpose"].str.replace("_", " ")[::-1], purpose["default_rate"][::-1] * 100, color=NAVY_MID)
    _style_ax(ax, "Default rate by purpose")
    ax.set_xlabel("%")

    ax = fig.add_subplot(gs[0, 2])
    term = term.sort_values("term_months")
    ax.bar(term["term_months"].astype(int).astype(str) + " mo", term["default_rate"] * 100, color=NAVY)
    _style_ax(ax, "Default rate by term")
    ax.set_ylabel("%")

    ax = fig.add_subplot(gs[1, 0])
    income = income.dropna(subset=["income_bucket"]).copy()
    income_order = ["<=40k", "40-60k", "60-85k", "85-125k", ">125k"]
    income["income_bucket"] = income["income_bucket"].astype(str)
    income["_ord"] = income["income_bucket"].map({k: i for i, k in enumerate(income_order)})
    income = income.sort_values("_ord")
    ax.barh(income["income_bucket"], income["default_rate"] * 100, color=NAVY_MID)
    _style_ax(ax, "Default rate by income bucket")
    ax.set_xlabel("%")

    ax = fig.add_subplot(gs[1, 1])
    dti = dti.dropna(subset=["dti_bucket"]).copy()
    dti_order = ["<=10", "10-15", "15-20", "20-25", "25-30", ">30"]
    dti["dti_bucket"] = dti["dti_bucket"].astype(str)
    dti["_ord"] = dti["dti_bucket"].map({k: i for i, k in enumerate(dti_order)})
    dti = dti.sort_values("_ord")
    ax.barh(dti["dti_bucket"], dti["default_rate"] * 100, color=RISK)
    _style_ax(ax, "Default rate by DTI bucket")
    ax.set_xlabel("%")

    ax = fig.add_subplot(gs[1, 2])
    x = np.arange(len(el))
    ax.bar(x - 0.18, el["ead"] / 1e9, width=0.36, color=NAVY, label="Exposure $B")
    ax.bar(x + 0.18, el["expected_loss"] / 1e9, width=0.36, color=RISK, label="EL $B")
    ax.set_xticks(x, el["grade"])
    _style_ax(ax, "Exposure and expected loss by grade")
    ax.legend(fontsize=8, frameon=False)

    _footer(fig)
    return _save(fig, "dashboard_02_credit_risk_segmentation.png")


def dashboard_03() -> Path:
    curves = _read("tableau_vintage.csv")
    summary = _read("tableau_vintage_summary.csv").dropna(subset=["vintage"])

    fig = plt.figure(figsize=(16, 10.2))
    _header(
        fig,
        "Credit Risk & Loan Default Analysis  ·  Vintage Performance",
        "Which vintages are underperforming and when default risk emerges",
    )
    _insight(fig, "vintage", y=0.86)
    gs = GridSpec(2, 1, left=0.07, right=0.98, top=0.84, bottom=0.07, hspace=0.32, figure=fig)

    ax = fig.add_subplot(gs[0, 0])
    curves = curves.dropna(subset=["vintage"])
    for vintage, part in curves.groupby("vintage"):
        ax.plot(part["loan_age_months"], part["cumulative_default_rate"] * 100, linewidth=1.4, label=str(int(vintage)))
    _style_ax(ax, "Cumulative default rate by loan age")
    ax.set_xlabel("Loan age (months)")
    ax.set_ylabel("%")
    ax.legend(ncol=6, fontsize=8, frameon=False, loc="upper left")

    ax = fig.add_subplot(gs[1, 0])
    if "cumulative_loss_rate" in curves.columns:
        for vintage, part in curves.groupby("vintage"):
            ax.plot(part["loan_age_months"], part["cumulative_loss_rate"] * 100, linewidth=1.4, label=str(int(vintage)))
        _style_ax(ax, "Cumulative loss rate by loan age")
        ax.set_ylabel("%")
    else:
        vint = summary.sort_values("vintage")
        ax.bar(vint["vintage"].astype(int).astype(str), vint["default_rate"] * 100, color=RISK)
        _style_ax(ax, "Matured default rate by vintage")
        ax.set_ylabel("%")
    ax.set_xlabel("Loan age (months)" if "cumulative_loss_rate" in curves.columns else "Vintage")

    _footer(fig)
    return _save(fig, "dashboard_03_vintage_performance.png")


def dashboard_04() -> Path:
    el_grade = _read("tableau_el_by_grade.csv").sort_values("grade")
    el_state = _read("tableau_el_by_state.csv").nlargest(12, "expected_loss")
    el_vint = _read("tableau_el_by_vintage.csv").dropna(subset=["vintage"]).sort_values("vintage")
    conc = _read("tableau_concentration_by_grade.csv")
    seg = _read("tableau_risk_segmentation.csv")

    fig = plt.figure(figsize=(16, 10.2))
    _header(
        fig,
        "Credit Risk & Loan Default Analysis  ·  Expected Loss and Concentration",
        "Where PD, exposure and expected loss concentrate — and where to focus first",
    )
    _insight(fig, "expected_loss", y=0.86)
    gs = GridSpec(2, 3, left=0.06, right=0.98, top=0.84, bottom=0.06, wspace=0.32, hspace=0.38, figure=fig)

    ax = fig.add_subplot(gs[0, 0])
    ax.bar(el_grade["grade"], el_grade["expected_loss"] / 1e6, color=NAVY)
    _style_ax(ax, "Expected loss by grade ($M)")

    ax = fig.add_subplot(gs[0, 1])
    ax.barh(el_state["addr_state"][::-1], el_state["expected_loss"][::-1] / 1e6, color=NAVY_MID)
    _style_ax(ax, "Expected loss by state ($M)")

    ax = fig.add_subplot(gs[0, 2])
    ax.bar(el_vint["vintage"].astype(int).astype(str), el_vint["expected_loss"] / 1e6, color=RISK)
    _style_ax(ax, "Expected loss by vintage ($M)")

    ax = fig.add_subplot(gs[1, 0])
    ax.scatter(conc["funded_amount"] / 1e9, conc["default_rate"] * 100, s=90, c=NAVY, zorder=3)
    for _, row in conc.iterrows():
        ax.annotate(str(row["grade"]), (row["funded_amount"] / 1e9, row["default_rate"] * 100), fontsize=8, color=INK, xytext=(4, 4), textcoords="offset points")
    _style_ax(ax, "PD proxy vs exposure by grade")
    ax.set_xlabel("Funded ($B)")
    ax.set_ylabel("Default rate (%)")

    ax = fig.add_subplot(gs[1, 1:])
    top = seg.nlargest(8, "exposure") if "exposure" in seg.columns else seg.head(8)
    label_col = "segment" if "segment" in top.columns else top.columns[0]
    value_col = "exposure" if "exposure" in top.columns else top.select_dtypes("number").columns[0]
    ax.barh(top[label_col].astype(str)[::-1], top[value_col][::-1] / 1e9, color=NAVY_MID)
    _style_ax(ax, "Exposure by risk segment ($B)")
    ax.set_xlabel("$B")

    _footer(fig)
    return _save(fig, "dashboard_04_expected_loss_concentration.png")


def dashboard_05() -> Path:
    deciles = _read("tableau_risk_deciles.csv")
    cal = _read("tableau_calibration_curve.csv")
    pr = _read("tableau_pr_curve.csv")
    fi = _read("tableau_feature_importance.csv")
    preds = _read("tableau_model_predictions.csv")

    fig = plt.figure(figsize=(16, 10.2))
    _header(
        fig,
        "Credit Risk & Loan Default Analysis  ·  Default Probability Model",
        "Can origination-time information rank higher-risk loans, and are the probabilities usable?",
    )
    _insight(fig, "model", y=0.86)
    gs = GridSpec(2, 3, left=0.06, right=0.98, top=0.84, bottom=0.06, wspace=0.32, hspace=0.38, figure=fig)

    band_order = ["Very Low", "Low", "Medium", "High", "Very High"]

    ax = fig.add_subplot(gs[0, 0])
    if "risk_band" in preds.columns:
        band = preds.groupby("risk_band", as_index=False)["predicted_pd"].mean()
        band["risk_band"] = pd.Categorical(band["risk_band"].astype(str), categories=band_order, ordered=True)
        band = band.sort_values("risk_band")
        ax.bar(band["risk_band"].astype(str), band["predicted_pd"] * 100, color=NAVY_MID)
        _style_ax(ax, "Average predicted PD by risk band")
    else:
        ax.bar(deciles["decile"].astype(str), deciles["average_predicted_pd"] * 100, color=NAVY_MID)
        _style_ax(ax, "Average predicted PD by decile")
    ax.set_ylabel("%")

    ax = fig.add_subplot(gs[0, 1])
    if "risk_band" in preds.columns and "actual_default" in preds.columns:
        actual = preds.groupby("risk_band", as_index=False)["actual_default"].mean()
        actual["risk_band"] = pd.Categorical(actual["risk_band"].astype(str), categories=band_order, ordered=True)
        actual = actual.sort_values("risk_band")
        ax.bar(actual["risk_band"].astype(str), actual["actual_default"] * 100, color=RISK)
        _style_ax(ax, "Actual default rate by risk band")
    else:
        ax.bar(deciles["decile"].astype(str), deciles["actual_default_rate"] * 100, color=RISK)
        _style_ax(ax, "Actual default rate by PD decile")
    ax.set_ylabel("%")

    ax = fig.add_subplot(gs[0, 2])
    xcol = "mean_predicted_pd" if "mean_predicted_pd" in cal.columns else cal.columns[0]
    ycol = "observed_default_rate" if "observed_default_rate" in cal.columns else cal.columns[1]
    ax.plot(cal[xcol] * 100, cal[ycol] * 100, color=NAVY, marker="o", markersize=4)
    ax.plot([0, 100], [0, 100], color=LINE, linestyle="--", linewidth=1)
    _style_ax(ax, "Calibration: predicted vs observed")
    ax.set_xlabel("Predicted PD (%)")
    ax.set_ylabel("Observed (%)")

    ax = fig.add_subplot(gs[1, 0])
    ax.plot(pr["recall"], pr["precision"], color=NAVY_MID, linewidth=1.8)
    _style_ax(ax, "Precision-recall curve")
    ax.set_xlabel("Recall")
    ax.set_ylabel("Precision")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)

    ax = fig.add_subplot(gs[1, 1])
    top = fi.nlargest(8, "importance_mean") if "importance_mean" in fi.columns else fi.head(8)
    name_col = "feature" if "feature" in top.columns else top.columns[0]
    val_col = "importance_mean" if "importance_mean" in top.columns else top.select_dtypes("number").columns[0]
    ax.barh(top[name_col].astype(str)[::-1], top[val_col][::-1], color=NAVY)
    _style_ax(ax, "Permutation importance")

    ax = fig.add_subplot(gs[1, 2])
    ax.bar(deciles["decile"].astype(str), deciles["actual_default_rate"] * 100, color=RISK)
    _style_ax(ax, "Actual default rate by PD decile")
    ax.set_xlabel("Decile")
    ax.set_ylabel("%")

    _footer(fig)
    return _save(fig, "dashboard_05_default_probability_model.png")


def dashboard_06() -> Path:
    recs = _read("tableau_recommendations.csv")
    el = _read("tableau_el_by_grade.csv").sort_values("grade")
    seg = _read("tableau_risk_segmentation.csv")

    fig = plt.figure(figsize=(16, 10.2))
    _header(
        fig,
        "Credit Risk & Loan Default Analysis  ·  Decision and Recommendations",
        "What should happen next, who owns it, and how progress will be measured",
    )
    _insight(fig, "decisions", y=0.86)

    table_ax = fig.add_axes([0.04, 0.42, 0.92, 0.41])
    table_ax.axis("off")
    table_ax.set_title("Priority recommendations", loc="left", fontsize=10, color=NAVY, fontweight="bold", pad=8)
    show = recs.copy()
    cols = [c for c in ["priority", "owner", "recommendation", "metric"] if c in show.columns]
    show = show[cols].head(5)
    cell_text = []
    for _, row in show.iterrows():
        cell_text.append([str(row[c])[:78] for c in cols])
    table = table_ax.table(
        cellText=cell_text,
        colLabels=[c.replace("_", " ").title() for c in cols],
        loc="upper center",
        cellLoc="left",
    )
    table.auto_set_font_size(False)
    table.set_fontsize(8)
    table.scale(1, 1.7)
    for (row, col), cell in table.get_celld().items():
        cell.set_edgecolor(LINE)
        if row == 0:
            cell.set_facecolor(NAVY)
            cell.set_text_props(color="white", fontweight="bold")
        else:
            cell.set_facecolor(CARD)

    gs = GridSpec(1, 2, left=0.06, right=0.98, top=0.38, bottom=0.07, wspace=0.28, figure=fig)
    ax = fig.add_subplot(gs[0, 0])
    top = seg.nlargest(8, "exposure") if "exposure" in seg.columns else seg.head(8)
    label_col = "segment" if "segment" in top.columns else top.columns[0]
    value_col = "exposure" if "exposure" in top.columns else top.select_dtypes("number").columns[0]
    ax.barh(top[label_col].astype(str)[::-1], top[value_col][::-1] / 1e9, color=NAVY_MID)
    _style_ax(ax, "Exposure by risk segment ($B)")

    ax = fig.add_subplot(gs[0, 1])
    ax.bar(el["grade"], el["expected_loss"] / 1e6, color=RISK)
    _style_ax(ax, "Expected loss by grade ($M)")

    _footer(fig)
    return _save(fig, "dashboard_06_decision_recommendations.png")


def build_dashboard_previews() -> list[Path]:
    return [
        dashboard_01(),
        dashboard_02(),
        dashboard_03(),
        dashboard_04(),
        dashboard_05(),
        dashboard_06(),
    ]
