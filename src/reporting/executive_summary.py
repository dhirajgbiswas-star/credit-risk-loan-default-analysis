"""Generate the executive summary and recommendation artefacts from calculated results."""

from __future__ import annotations

import json
import logging
from pathlib import Path

import pandas as pd

from src.config import MODEL_DIR, REPORT_DIR, TABLE_DIR

logger = logging.getLogger(__name__)


def _csv(name: str) -> pd.DataFrame:
    return pd.read_csv(TABLE_DIR / name)


def _pct(value) -> str:
    return f"{100 * float(value):.1f}%"


def _money(value) -> str:
    return f"${float(value):,.0f}"


def build_recommendation_matrix(kpis: dict, grade: pd.DataFrame, purpose: pd.DataFrame, vintage: pd.DataFrame) -> pd.DataFrame:
    el_grade = _csv("el_by_grade.csv")
    term = _csv("risk_by_term.csv")
    concentration = _csv("concentration_by_grade.csv")

    grade = grade.sort_values("default_rate", ascending=False)
    purpose_ok = purpose.loc[purpose["meets_sample_threshold"] == True].sort_values("default_rate", ascending=False)
    vintage_ok = vintage.dropna(subset=["default_rate"]).copy()
    if "matured_loans" in vintage_ok.columns:
        vintage_ok = vintage_ok.loc[vintage_ok["matured_loans"] >= 10000]
    vintage_ok = vintage_ok.sort_values("default_rate", ascending=False)

    prioritise = concentration.loc[concentration["concentration_quadrant"] == "Prioritise"]
    top_el = el_grade.sort_values("expected_loss", ascending=False).iloc[0]
    top_purpose = purpose_ok.iloc[0]
    top_purpose_el = _csv("el_by_purpose.csv").sort_values("expected_loss", ascending=False).iloc[0]
    weak_vintage = vintage_ok.iloc[0]
    long_term = term.sort_values("default_rate", ascending=False).iloc[0]
    short_term = term.sort_values("default_rate").iloc[0]
    grade_d = grade.loc[grade["grade"] == "D"].iloc[0] if "D" in set(grade["grade"]) else grade.iloc[0]
    focus_grade = prioritise.iloc[0] if not prioritise.empty else grade_d

    rows = [
        {
            "priority": "P1",
            "risk_opportunity": "High PD combined with material exposure",
            "evidence": (
                f"Grade {focus_grade['grade']} default rate {_pct(focus_grade['default_rate'])} "
                f"on {int(focus_grade['loan_count']):,} matured loans and {_money(focus_grade['funded_amount'])} funded exposure."
            ),
            "recommendation": "Review underwriting, documentation and risk-based pricing for the Prioritise-grade segment.",
            "action": "Credit policy review of grade-level cut-offs, pricing and exception governance.",
            "owner": "Head of Credit",
            "expected_outcome": "Lower default rate and improved risk-adjusted return where rate and exposure are both elevated.",
            "metric": "Default Rate / Expected Loss %",
            "target": "Move the Prioritise-grade default rate toward the book average without uncontrolled volume loss.",
            "timeline": "Immediate",
        },
        {
            "priority": "P1",
            "risk_opportunity": "Absolute expected-loss concentration in a large grade",
            "evidence": (
                f"Grade {top_el['grade']} contributes {_money(top_el['expected_loss'])} of base-case expected loss "
                f"on {_money(top_el['ead'])} matured exposure (PD {_pct(top_el['pd'])})."
            ),
            "recommendation": "Track expected-loss dollars, not only default rates, for the largest grade.",
            "action": "Portfolio Manager and Head of Credit to set an expected-loss appetite for the largest EL grade.",
            "owner": "Portfolio Manager",
            "expected_outcome": "Earlier intervention where loss dollars, rather than headline rates, dominate.",
            "metric": "Expected Loss $",
            "target": "Contain grade-level expected loss within the stated risk appetite.",
            "timeline": "Immediate",
        },
        {
            "priority": "P1",
            "risk_opportunity": "Term and purpose risk premia",
            "evidence": (
                f"{int(long_term['term_months'])}-month loans defaulted at {_pct(long_term['default_rate'])} versus "
                f"{_pct(short_term['default_rate'])} for {int(short_term['term_months'])}-month loans. "
                f"{top_purpose['purpose']} defaulted at {_pct(top_purpose['default_rate'])}. "
                f"{top_purpose_el['purpose']} still dominates purpose-level expected loss at {_money(top_purpose_el['expected_loss'])}."
            ),
            "recommendation": "Review pricing and eligibility for 60-month loans and higher-risk purposes, especially small business.",
            "action": "Product and credit joint review of term pricing, purpose eligibility and monitoring.",
            "owner": "Product Manager / Head of Credit",
            "expected_outcome": "Better alignment of price and policy with observed term and purpose risk.",
            "metric": "Expected Loss % / Default Rate",
            "target": "Reduce the 60-month and small-business expected-loss percentages.",
            "timeline": "Immediate",
        },
        {
            "priority": "P2",
            "risk_opportunity": "Weaker recent vintages after allowing for sample size",
            "evidence": (
                f"Vintage {int(weak_vintage['vintage'])} matured default rate {_pct(weak_vintage['default_rate'])} "
                f"on {int(weak_vintage['matured_loans']):,} matured loans."
            ),
            "recommendation": "Complete a vintage deep-dive controlling for grade mix and loan age.",
            "action": "Risk Analytics to compare age-adjusted vintage curves after mix adjustment.",
            "owner": "Risk Analytics",
            "expected_outcome": "Identify whether underperformance is mix, underwriting or environment.",
            "metric": "Vintage Default Rate",
            "target": "Explain the gap versus better-performing large vintages.",
            "timeline": "Near-term",
        },
        {
            "priority": "P3",
            "risk_opportunity": "Model monitoring and calibration",
            "evidence": (
                f"Matured default rate {_pct(kpis['default_rate'])} on {int(kpis['matured_loan_count']):,} loans. "
                "Class-weighted scores rank risk (bottom decile 3.5% versus top decile 46.9%) but overstate absolute PD."
            ),
            "recommendation": "Use the model for ranking and enhanced review, then monitor calibration separately.",
            "action": "Model Risk to track PR-AUC, Brier score, decile ordering and calibration drift.",
            "owner": "Model Risk",
            "expected_outcome": "Maintain ranking quality as the book and economy change.",
            "metric": "PR-AUC / Brier Score",
            "target": "No material deterioration versus the validation snapshot.",
            "timeline": "Monitor / long-term",
        },
    ]
    return pd.DataFrame(rows)


def _write_decision_tables(
    kpis: dict,
    grade: pd.DataFrame,
    purpose: pd.DataFrame,
    vintage: pd.DataFrame,
    el_grade: pd.DataFrame,
    term: pd.DataFrame,
    recs: pd.DataFrame,
) -> None:
    d_row = grade.loc[grade["grade"] == "D"].iloc[0]
    c_row = el_grade.loc[el_grade["grade"] == "C"].iloc[0]
    a_row = grade.loc[grade["grade"] == "A"].iloc[0]
    g_row = grade.loc[grade["grade"] == "G"].iloc[0]
    sb = purpose.loc[purpose["purpose"] == "small_business"].iloc[0]
    dc = purpose.loc[purpose["purpose"] == "debt_consolidation"].iloc[0]
    long_term = term.iloc[0]
    weak_v = vintage.sort_values("default_rate", ascending=False).iloc[0]
    el_purpose = _csv("el_by_purpose.csv")
    el_term = _csv("el_by_term.csv")
    base_el = _csv("el_sensitivity.csv")
    base_el = base_el.loc[base_el["scenario"] == "Base", "expected_loss"].iloc[0]

    segmentation = pd.DataFrame(
        [
            {
                "segment": "Grade D",
                "pd": d_row["default_rate"],
                "exposure": d_row["funded_amount"],
                "expected_loss": float(el_grade.loc[el_grade["grade"] == "D", "expected_loss"].iloc[0]),
                "risk_level": "High",
                "business_action": "Prioritise underwriting and pricing review",
            },
            {
                "segment": "Grade C",
                "pd": float(c_row["pd"]),
                "exposure": float(c_row["ead"]),
                "expected_loss": float(c_row["expected_loss"]),
                "risk_level": "Medium-High",
                "business_action": "Optimise with an expected-loss appetite",
            },
            {
                "segment": "Grade G",
                "pd": g_row["default_rate"],
                "exposure": g_row["funded_amount"],
                "expected_loss": float(el_grade.loc[el_grade["grade"] == "G", "expected_loss"].iloc[0]),
                "risk_level": "Very High",
                "business_action": "Investigate; small exposure relative to loss dollars elsewhere",
            },
            {
                "segment": "60-month term",
                "pd": long_term["default_rate"],
                "exposure": long_term["funded_amount"],
                "expected_loss": float(el_term.sort_values("expected_loss", ascending=False).iloc[0]["expected_loss"]),
                "risk_level": "High",
                "business_action": "Review term pricing and eligibility",
            },
            {
                "segment": "Small business",
                "pd": sb["default_rate"],
                "exposure": sb["funded_amount"],
                "expected_loss": float(el_purpose.loc[el_purpose["purpose"] == "small_business", "expected_loss"].iloc[0]),
                "risk_level": "High",
                "business_action": "Product and credit eligibility review",
            },
            {
                "segment": "Debt consolidation",
                "pd": dc["default_rate"],
                "exposure": dc["funded_amount"],
                "expected_loss": float(el_purpose.loc[el_purpose["purpose"] == "debt_consolidation", "expected_loss"].iloc[0]),
                "risk_level": "Medium",
                "business_action": "Monitor; largest purpose-level expected-loss dollars",
            },
            {
                "segment": "Grade A",
                "pd": a_row["default_rate"],
                "exposure": a_row["funded_amount"],
                "expected_loss": float(el_grade.loc[el_grade["grade"] == "A", "expected_loss"].iloc[0]),
                "risk_level": "Low",
                "business_action": "Optimise growth within risk appetite",
            },
        ]
    )
    segmentation.to_csv(TABLE_DIR / "risk_segmentation.csv", index=False)

    decisions = pd.DataFrame(
        [
            {
                "business_question": "Where is credit risk concentrated?",
                "evidence": f"Grade A {_pct(a_row['default_rate'])} versus grade G {_pct(g_row['default_rate'])}; grade D is high rate and high exposure.",
                "insight": "Risk is graded, but policy should follow both rate and exposure.",
                "decision": "Prioritise grade D; investigate E-G; set an EL appetite for grade C.",
                "action": "Credit policy and pricing review",
                "owner": "Head of Credit",
                "kpi": "Default Rate / Expected Loss $",
            },
            {
                "business_question": "How large is the potential loss?",
                "evidence": f"Base-case expected loss {_money(base_el)} at 50% LGD.",
                "insight": "A 10% expected-loss ratio on matured exposure is material for unsecured consumer credit.",
                "decision": "Use expected-loss dollars as the North Star for management attention.",
                "action": "Monthly EL dashboard",
                "owner": "Chief Risk Officer",
                "kpi": "Expected Loss $ / Expected Loss %",
            },
            {
                "business_question": "Does term change the risk picture?",
                "evidence": f"60-month default rate {_pct(long_term['default_rate'])} versus 16.0% on 36-month loans.",
                "insight": "Term is one of the strongest observable differentiators after grade.",
                "decision": "Review 60-month pricing and eligibility.",
                "action": "Product pricing review",
                "owner": "Product Manager",
                "kpi": "Default Rate by Term",
            },
            {
                "business_question": "Which vintages need investigation?",
                "evidence": f"Vintage {int(weak_v['vintage'])} defaulted at {_pct(weak_v['default_rate'])} among large matured cohorts.",
                "insight": "2018 looks better only because it is less mature.",
                "decision": "Age-adjust all vintage comparisons.",
                "action": "Vintage deep-dive",
                "owner": "Risk Analytics",
                "kpi": "Age-adjusted vintage default rate",
            },
            {
                "business_question": "Can origination data rank higher-risk loans?",
                "evidence": "Validation default rate 3.5% in the lowest PD decile versus 46.9% in the highest.",
                "insight": "The model is useful for ranking and review queues, not for automated decline or capital PD.",
                "decision": "Adopt scores for enhanced monitoring with human oversight.",
                "action": "Threshold and monitoring design",
                "owner": "Model Risk",
                "kpi": "PR-AUC / decile lift",
            },
        ]
    )
    decisions.to_csv(TABLE_DIR / "decision_framework.csv", index=False)
    recs.to_csv(TABLE_DIR / "recommendation_matrix.csv", index=False)


def write_executive_outputs() -> Path:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    kpis = _csv("portfolio_kpis.csv").iloc[0].to_dict()
    grade = _csv("risk_by_grade.csv")
    purpose = _csv("risk_by_purpose.csv")
    vintage = _csv("vintage_summary.csv")
    sensitivity = _csv("el_sensitivity.csv")
    base = sensitivity.loc[sensitivity["scenario"] == "Base"].iloc[0].to_dict()
    recs = build_recommendation_matrix(kpis, grade, purpose, vintage)
    recs.to_csv(TABLE_DIR / "recommendation_matrix.csv", index=False)

    best_grade = grade.sort_values("default_rate").iloc[0]
    worst_grade = grade.sort_values("default_rate", ascending=False).iloc[0]
    if "meets_sample_threshold" in purpose.columns:
        purpose_ok = purpose.loc[purpose["meets_sample_threshold"] == True]
    else:
        purpose_ok = purpose
    worst_purpose = purpose_ok.sort_values("default_rate", ascending=False).iloc[0]
    vintage_ok = vintage.dropna(subset=["default_rate"]).copy()
    if "matured_loans" in vintage_ok.columns:
        vintage_large = vintage_ok.loc[vintage_ok["matured_loans"] >= 10000]
    else:
        vintage_large = vintage_ok
    best_vintage = vintage_large.sort_values("default_rate").iloc[0]
    worst_vintage = vintage_large.sort_values("default_rate", ascending=False).iloc[0]
    el_grade = _csv("el_by_grade.csv").sort_values("expected_loss", ascending=False)
    term = _csv("risk_by_term.csv").sort_values("default_rate", ascending=False)
    deciles = _csv("risk_deciles.csv") if (TABLE_DIR / "risk_deciles.csv").exists() else pd.DataFrame()

    model_summary = {}
    summary_path = MODEL_DIR / "training_summary.json"
    if summary_path.exists():
        model_summary = json.loads(summary_path.read_text(encoding="utf-8"))

    text = f"""# Executive Summary
# Credit Risk & Loan Default Analysis

## Business Situation
Lending institutions need to grow originations without accepting unmanaged credit loss. This review of the Lending Club accepted-loan book measures where default risk and expected loss are concentrated, how vintages perform as loans age, and whether origination-time information can rank higher-risk loans.

## Key Finding 1
The matured book default rate is {_pct(kpis['default_rate'])} ({int(kpis['default_count']):,} defaults on {int(kpis['matured_loan_count']):,} matured loans). Overall funded amount is {_money(kpis['funded_amount'])} across {int(kpis['loan_count']):,} originated loans.

## Key Finding 2
Credit risk is highly graded. Grade {best_grade['grade']} defaulted at {_pct(best_grade['default_rate'])}, while grade {worst_grade['grade']} defaulted at {_pct(worst_grade['default_rate'])}.

## Key Finding 3
Purpose and term still differentiate risk after looking at volume. The highest observed purpose-level default rate is {worst_purpose['purpose']} at {_pct(worst_purpose['default_rate'])}.

## Risk Concentration
Management should not look at default rates alone. Large, mid-risk grades can contribute more expected-loss dollars than small, very high-rate niches. Grade-level funded exposure and default rates are both required to set priorities.

## Expected Loss
Using a documented base-case LGD of {100 * float(base['lgd_assumption']):.0f}% and the observed matured PD of {_pct(base['pd'])}, portfolio expected loss is {_money(base['expected_loss'])} ({_pct(base['expected_loss_pct'])} of matured funded exposure). Optimistic and adverse LGD cases are provided in the sensitivity table. These LGD values are analytical assumptions, not official Lending Club metrics.

## Model Performance
"""
    if model_summary:
        best = model_summary.get("best_model", "n/a")
        chosen = model_summary.get("selected_threshold", {})
        text += (
            f"The selected origination-time model is {best}. "
            f"Validation PR-AUC is {chosen.get('pr_auc', 'n/a')} and ROC-AUC is {chosen.get('roc_auc', 'n/a')}. "
            f"The operating threshold of {chosen.get('threshold', 'n/a')} was chosen to minimise expected classification cost.\n\n"
        )
    else:
        text += "Train the default-probability model to populate validation metrics.\n\n"

    text += f"""## Business Judgement
Observed default risk rises sharply as grade weakens: {best_grade['grade']} at {_pct(best_grade['default_rate'])} versus {worst_grade['grade']} at {_pct(worst_grade['default_rate'])}. Absolute expected loss is still dominated by large grades. Grade {el_grade.iloc[0]['grade']} contributes the most base-case expected-loss dollars ({_money(el_grade.iloc[0]['expected_loss'])}), while grade D is the high-rate, high-exposure cell that should be first in the policy queue. {int(term.iloc[0]['term_months'])}-month loans defaulted at {_pct(term.iloc[0]['default_rate'])}, about twice the shorter-term rate. Newer vintages must be read on an age-adjusted basis; among large matured vintages, {int(worst_vintage['vintage'])} is the weakest at {_pct(worst_vintage['default_rate'])}.

## Recommendation
1. Review underwriting and pricing for grade D and other Prioritise cells.
2. Set an expected-loss appetite for grade C, which dominates loss dollars.
3. Review 60-month pricing and small-business eligibility.
4. Investigate the {int(worst_vintage['vintage'])} vintage after controlling for grade mix.
5. Use the PD model as a ranking and monitoring tool, not as an automated decline engine.

## Expected Impact
A tighter link between price, policy and observed risk should reduce expected loss percentage in the weakest high-exposure segments and improve risk-adjusted portfolio performance.

## Monitoring
Track Expected Loss $, Expected Loss %, matured default rate, vintage curves at comparable loan age, PR-AUC, Brier score, top-versus-bottom decile default rates, and high-risk/high-exposure segment share.

## Vintage Reference
Best large matured vintage (at least 10,000 matured loans): {int(best_vintage['vintage'])} at {_pct(best_vintage['default_rate'])}. Weakest large matured vintage: {int(worst_vintage['vintage'])} at {_pct(worst_vintage['default_rate'])}.
"""
    if not deciles.empty:
        bottom = deciles.sort_values("decile").iloc[0]
        top = deciles.sort_values("decile").iloc[-1]
        text += (
            f"\n## Model Ranking\nValidation default rate rises from {_pct(bottom['actual_default_rate'])} "
            f"in the lowest predicted-PD decile to {_pct(top['actual_default_rate'])} in the highest decile. "
            "Class weighting improves recall and ranking but overstates absolute probabilities, so scores should be used for ordering and review rather than as a calibrated PD for capital.\n"
        )

    _write_decision_tables(kpis, grade, purpose, vintage_large, el_grade, term, recs)
    output = REPORT_DIR / "executive_summary.md"
    output.write_text(text, encoding="utf-8")
    logger.info("Wrote %s", output)
    return output
