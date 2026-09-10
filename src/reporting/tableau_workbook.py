"""Generate Tableau Desktop-compatible .twb workbooks from project CSV extracts."""

from __future__ import annotations

import hashlib
import logging
import re
import shutil
from pathlib import Path
from xml.sax.saxutils import escape

import pandas as pd
from lxml import etree

from src.config import PROJECT_ROOT, TABLE_DIR, TABLEAU_DIR

logger = logging.getLogger(__name__)

TABLEAU_OUTPUT_DIR = PROJECT_ROOT / "tableau"
TABLEAU_XML_VERSION = "18.1"
TABLEAU_SOURCE_BUILD = "20262.26.0708.1337"
USER_NS = "http://www.tableausoftware.com/xml/user"

DIMENSION_FIELDS = {
    "grade",
    "purpose",
    "addr_state",
    "segment",
    "segment_type",
    "risk_band",
    "scenario",
    "priority",
    "owner",
    "timeline",
    "metric",
    "recommendation",
    "action",
    "evidence",
    "risk_opportunity",
    "target",
    "vintage",
    "issue_year",
    "issue_quarter",
    "income_bucket",
    "dti_bucket",
    "term_months",
    "employment_length_bucket",
    "loan_amount_bucket",
    "interest_rate_bucket",
    "feature",
    "direction",
    "decile",
    "model",
    "selection_rule",
    "term",
    "home_ownership",
    "verification_status",
    "application_type",
    "concentration_quadrant",
    "risk_level",
    "business_action",
    "business_question",
    "insight",
    "decision",
    "kpi",
    "loan_age_months",
    "meets_sample_threshold",
    "high_risk",
    "high_exposure",
}

MARK_CLASS = {
    "bar": "Bar",
    "line": "Line",
    "circle": "Circle",
    "text": "Text",
    "automatic": "Automatic",
}

NAVY = "#1B365D"
NAVY_MID = "#2F5D8A"
INK = "#1C2430"
MUTED = "#5B6B7C"
CANVAS = "#E8EDF3"
CARD = "#FFFFFF"
LINE = "#D4DCE6"
RISK = "#8C2F3B"
FONT = "Tableau Book"
FONT_MED = "Tableau Medium"
DASH_WIDTH = 1600
DASH_PAD = 16
DASH_GAP = 12
FOOTER_TEXT = (
    "Lending Club accepted loans, 2007–2018  ·  Matured outcomes  ·  "
    "Base-case LGD 50%  ·  Public Kaggle extract"
)


def stage_supplementary_extracts() -> None:
    TABLEAU_DIR.mkdir(parents=True, exist_ok=True)
    copies = {
        "risk_by_term.csv": "tableau_risk_by_term.csv",
        "risk_by_income_bucket.csv": "tableau_risk_by_income_bucket.csv",
        "risk_by_dti_bucket.csv": "tableau_risk_by_dti_bucket.csv",
        "risk_by_employment_length.csv": "tableau_risk_by_employment_length.csv",
        "concentration_by_grade.csv": "tableau_concentration_by_grade.csv",
        "concentration_by_purpose.csv": "tableau_concentration_by_purpose.csv",
        "vintage_summary.csv": "tableau_vintage_summary.csv",
        "calibration_curve.csv": "tableau_calibration_curve.csv",
        "risk_deciles.csv": "tableau_risk_deciles.csv",
        "permutation_importance.csv": "tableau_feature_importance.csv",
        "threshold_analysis.csv": "tableau_threshold_analysis.csv",
        "risk_segmentation.csv": "tableau_risk_segmentation.csv",
        "decision_framework.csv": "tableau_decision_framework.csv",
        "model_comparison.csv": "tableau_model_comparison.csv",
        "el_by_grade.csv": "tableau_el_by_grade.csv",
        "el_by_purpose.csv": "tableau_el_by_purpose.csv",
        "el_by_state.csv": "tableau_el_by_state.csv",
        "el_by_vintage.csv": "tableau_el_by_vintage.csv",
    }
    for source, target in copies.items():
        src = TABLE_DIR / source
        if src.exists():
            shutil.copy2(src, TABLEAU_DIR / target)

    pr_path = TABLE_DIR / "pr_curve.csv"
    if pr_path.exists():
        pr = pd.read_csv(pr_path)
        pr.iloc[:: max(1, len(pr) // 300)].to_csv(TABLEAU_DIR / "tableau_pr_curve.csv", index=False)

    roc_path = TABLE_DIR / "roc_curve.csv"
    if roc_path.exists():
        roc = pd.read_csv(roc_path)
        roc.iloc[:: max(1, len(roc) // 300)].to_csv(TABLEAU_DIR / "tableau_roc_curve.csv", index=False)


def _col_specs(frame: pd.DataFrame) -> list[dict]:
    specs: list[dict] = []
    for column in frame.columns:
        series = frame[column]
        if pd.api.types.is_bool_dtype(series):
            datatype, role = "boolean", "dimension"
        elif pd.api.types.is_integer_dtype(series):
            datatype, role = "integer", "measure"
        elif pd.api.types.is_float_dtype(series):
            datatype, role = "real", "measure"
        else:
            datatype, role = "string", "dimension"
        if column in DIMENSION_FIELDS or str(column).endswith("_bucket"):
            role = "dimension"
        specs.append({"caption": str(column), "datatype": datatype, "role": role})
    return specs


def _csv_datasource(caption: str, csv_name: str) -> dict:
    csv_path = TABLEAU_DIR / csv_name
    if not csv_path.exists():
        raise FileNotFoundError(f"Missing Tableau extract: {csv_path}")
    frame = pd.read_csv(csv_path)
    return {
        "caption": caption,
        "csv_name": csv_name,
        "directory": str(TABLEAU_DIR.resolve()),
        "columns": _col_specs(frame),
    }


def _bar(name: str, datasource: str, dimension: str, measure: str, title: str, agg: str = "AVG") -> dict:
    return {
        "name": name,
        "datasource": datasource,
        "mark_type": "bar",
        "rows": [dimension],
        "columns": [f"{agg}({measure})"],
        "title": title,
    }


def _line(name: str, datasource: str, x_field: str, y_field: str, color: str | None, title: str) -> dict:
    spec = {
        "name": name,
        "datasource": datasource,
        "mark_type": "line",
        "columns": [x_field],
        "rows": [f"AVG({y_field})"],
        "title": title,
    }
    if color:
        spec["color"] = [color]
    return spec


def _scatter(name: str, datasource: str, x_field: str, y_field: str, color: str | None, title: str) -> dict:
    spec = {
        "name": name,
        "datasource": datasource,
        "mark_type": "circle",
        "columns": [f"SUM({x_field})"],
        "rows": [f"AVG({y_field})"],
        "title": title,
    }
    if color:
        spec["color"] = [color]
    return spec


def _compact_money(value: float) -> str:
    abs_value = abs(value)
    if abs_value >= 1_000_000_000:
        return f"${value / 1_000_000_000:,.2f}B"
    if abs_value >= 1_000_000:
        return f"${value / 1_000_000:,.1f}M"
    return f"${value:,.0f}"


def _compact_count(value: float) -> str:
    if abs(value) >= 1_000_000:
        return f"{value / 1_000_000:,.2f}M"
    return f"{value:,.0f}"


def _insight_items(dashboard_key: str) -> list[tuple[str, str]]:
    blocks = {
        "executive": [
            ("KEY INSIGHT", "Grade D combines a 30.4% default rate with $3.07B exposure and should be prioritised."),
            ("EVIDENCE", "Matured default rate 20.0%; base-case expected loss $1.94B (10.0% of matured funded exposure)."),
            ("BUSINESS MEANING", "Default rates alone understate loss concentration in large grades such as C."),
            ("RECOMMENDED ACTION", "Review underwriting and pricing for Prioritise segments."),
        ],
        "segmentation": [
            ("KEY INSIGHT", "60-month loans default at 32.5% versus 16.0% for 36-month loans."),
            ("EVIDENCE", "Small business purpose defaults at 29.9%; DTI above 30% defaults at 29.2%."),
            ("BUSINESS MEANING", "Term and purpose remain strong risk differentiators after grade."),
            ("RECOMMENDED ACTION", "Review term pricing and purpose eligibility."),
        ],
        "vintage": [
            ("KEY INSIGHT", "Default risk emerges between loan ages 12 and 36 months."),
            ("EVIDENCE", "Among large matured vintages, 2016 is weakest at 23.3% and 2010 is strongest at 14.0%."),
            ("BUSINESS MEANING", "Newer vintages must be compared at the same loan age."),
            ("RECOMMENDED ACTION", "Investigate 2016 after controlling for grade mix."),
        ],
        "expected_loss": [
            ("KEY INSIGHT", "Grade C contributes the largest expected-loss dollars ($608M base case)."),
            ("EVIDENCE", "Grade D expected loss is 15.2% of exposure; debt consolidation dominates purpose-level EL."),
            ("BUSINESS MEANING", "PD × exposure × expected loss should drive management focus."),
            ("RECOMMENDED ACTION", "Set an expected-loss appetite for high-dollar segments."),
        ],
        "model": [
            ("KEY INSIGHT", "The model ranks risk well but overstates absolute probabilities."),
            ("EVIDENCE", "Validation default rate rises from 3.5% to 46.9% across PD deciles; PR-AUC 0.387."),
            ("BUSINESS MEANING", "Use scores for review queues, not automated decline."),
            ("RECOMMENDED ACTION", "Monitor decile lift, PR-AUC and calibration monthly."),
        ],
        "decisions": [
            ("KEY INSIGHT", "P1 actions target grade D, grade C expected-loss dollars, and term/purpose pricing."),
            ("EVIDENCE", "The recommendation matrix links evidence, owner and metric for each action."),
            ("BUSINESS MEANING", "Management can move from finding to owner to KPI."),
            ("RECOMMENDED ACTION", "Assign owners and track Expected Loss % and Default Rate."),
        ],
    }
    return blocks[dashboard_key]


def _header_zone(title: str, subtitle: str, width: int, y: int = 10) -> dict:
    return {
        "role": "header",
        "x": DASH_PAD,
        "y": y,
        "w": width - 2 * DASH_PAD,
        "h": 54,
        "runs": [
            {
                "text": title,
                "fontsize": "16",
                "bold": True,
                "color": CARD,
                "fontname": FONT_MED,
            },
            {
                "text": subtitle,
                "fontsize": "11",
                "color": "#D7DEE8",
                "fontname": FONT,
            },
        ],
    }


def _insight_zone(dashboard_key: str, width: int, y: int, height: int = 108) -> dict:
    runs: list[dict] = []
    for index, (label, body) in enumerate(_insight_items(dashboard_key)):
        runs.append(
            {
                "text": label,
                "fontsize": "9",
                "bold": True,
                "color": NAVY,
                "fontname": FONT_MED,
            }
        )
        runs.append(
            {
                "text": f"  {body}",
                "fontsize": "11",
                "color": INK,
                "fontname": FONT,
                "same_line": True,
            }
        )
        if index == 0:
            runs[0]["fontsize"] = "10"
    return {
        "role": "insight",
        "x": DASH_PAD,
        "y": y,
        "w": width - 2 * DASH_PAD,
        "h": height,
        "runs": runs,
    }


def _footer_zone(width: int, height: int) -> dict:
    return {
        "role": "footer",
        "x": DASH_PAD,
        "y": height - 26,
        "w": width - 2 * DASH_PAD,
        "h": 18,
        "runs": [{"text": FOOTER_TEXT, "fontsize": "9", "color": MUTED, "fontname": FONT}],
    }


def _kpi_zones(kpi: pd.Series, y: int, width: int) -> list[dict]:
    cards = [
        ("FUNDED AMOUNT", _compact_money(float(kpi["funded_amount"])), NAVY, NAVY),
        ("LOAN COUNT", _compact_count(float(kpi["loan_count"])), NAVY, NAVY),
        ("DEFAULT RATE", f"{100 * kpi['default_rate']:.1f}%", RISK, RISK),
        ("CHARGED-OFF RATE", f"{100 * kpi['charged_off_rate']:.1f}%", RISK, RISK),
        ("EXPECTED LOSS $", _compact_money(float(kpi["expected_loss"])), RISK, NAVY),
        ("EXPECTED LOSS %", f"{100 * kpi['expected_loss_pct']:.1f}%", RISK, RISK),
        ("AVERAGE PD", f"{100 * kpi['average_pd']:.1f}%", NAVY_MID, NAVY),
    ]
    count = len(cards)
    usable = width - 2 * DASH_PAD - (count - 1) * DASH_GAP
    card_w = usable // count
    zones = []
    for index, (label, value, accent, value_color) in enumerate(cards):
        zones.append(
            {
                "role": "kpi",
                "accent": accent,
                "x": DASH_PAD + index * (card_w + DASH_GAP),
                "y": y,
                "w": card_w,
                "h": 84,
                "runs": [
                    {"text": label, "fontsize": "9", "color": MUTED, "fontname": FONT},
                    {
                        "text": value,
                        "fontsize": "20",
                        "bold": True,
                        "color": value_color,
                        "fontname": FONT_MED,
                    },
                ],
            }
        )
    return zones


def _chart_pair(left: str, right: str, y: int, width: int, height: int = 236) -> list[dict]:
    chart_w = (width - 2 * DASH_PAD - DASH_GAP) // 2
    return [
        {"role": "chart", "worksheet": left, "x": DASH_PAD, "y": y, "w": chart_w, "h": height},
        {
            "role": "chart",
            "worksheet": right,
            "x": DASH_PAD + chart_w + DASH_GAP,
            "y": y,
            "w": chart_w,
            "h": height,
        },
    ]


def _chart_triple(names: list[str], y: int, width: int, height: int = 220) -> list[dict]:
    gaps = DASH_GAP * (len(names) - 1)
    chart_w = (width - 2 * DASH_PAD - gaps) // len(names)
    return [
        {
            "role": "chart",
            "worksheet": name,
            "x": DASH_PAD + index * (chart_w + DASH_GAP),
            "y": y,
            "w": chart_w,
            "h": height,
        }
        for index, name in enumerate(names)
    ]


def _chart_full(name: str, y: int, width: int, height: int) -> dict:
    return {
        "role": "chart",
        "worksheet": name,
        "x": DASH_PAD,
        "y": y,
        "w": width - 2 * DASH_PAD,
        "h": height,
    }


def build_master_workbook_spec() -> dict:
    kpi = pd.read_csv(TABLEAU_DIR / "tableau_kpi_summary.csv").iloc[0]

    datasources = [
        _csv_datasource("KPI Summary", "tableau_kpi_summary.csv"),
        _csv_datasource("Volume by Year", "tableau_volume_by_year.csv"),
        _csv_datasource("Vintage Summary", "tableau_vintage_summary.csv"),
        _csv_datasource("Risk by Grade", "tableau_risk_by_grade.csv"),
        _csv_datasource("Risk by Purpose", "tableau_risk_by_purpose.csv"),
        _csv_datasource("Risk by Term", "tableau_risk_by_term.csv"),
        _csv_datasource("Risk by Income", "tableau_risk_by_income_bucket.csv"),
        _csv_datasource("Risk by DTI", "tableau_risk_by_dti_bucket.csv"),
        _csv_datasource("Risk by State", "tableau_risk_by_state.csv"),
        _csv_datasource("Concentration by Grade", "tableau_concentration_by_grade.csv"),
        _csv_datasource("Expected Loss by Grade", "tableau_el_by_grade.csv"),
        _csv_datasource("Expected Loss by Purpose", "tableau_el_by_purpose.csv"),
        _csv_datasource("Expected Loss by State", "tableau_el_by_state.csv"),
        _csv_datasource("Expected Loss by Vintage", "tableau_el_by_vintage.csv"),
        _csv_datasource("Vintage Curves", "tableau_vintage.csv"),
        _csv_datasource("Model Predictions", "tableau_model_predictions.csv"),
        _csv_datasource("Calibration Curve", "tableau_calibration_curve.csv"),
        _csv_datasource("PR Curve", "tableau_pr_curve.csv"),
        _csv_datasource("Feature Importance", "tableau_feature_importance.csv"),
        _csv_datasource("Risk Deciles", "tableau_risk_deciles.csv"),
        _csv_datasource("Threshold Analysis", "tableau_threshold_analysis.csv"),
        _csv_datasource("Recommendations", "tableau_recommendations.csv"),
        _csv_datasource("Risk Segmentation", "tableau_risk_segmentation.csv"),
    ]

    worksheets = [
        _bar("Portfolio Volume Trend", "Volume by Year", "issue_year", "loan_count", "Loan Count by Issue Year", "SUM"),
        _bar("Funded Amount Trend", "Volume by Year", "issue_year", "funded_amount", "Funded Amount by Issue Year", "SUM"),
        _bar("Default Rate by Vintage", "Vintage Summary", "vintage", "default_rate", "Matured Default Rate by Vintage"),
        _bar("Expected Loss by Grade", "Expected Loss by Grade", "grade", "expected_loss", "Expected Loss by Grade", "SUM"),
        _scatter(
            "Risk Concentration Matrix",
            "Concentration by Grade",
            "funded_amount",
            "default_rate",
            "concentration_quadrant",
            "Default Rate vs Funded Exposure by Grade",
        ),
        _bar("Top Purpose Expected Loss", "Expected Loss by Purpose", "purpose", "expected_loss", "Expected Loss by Purpose", "SUM"),
        _bar("Default Rate by Grade", "Risk by Grade", "grade", "default_rate", "Default Rate by Grade"),
        _bar("Default Rate by Purpose", "Risk by Purpose", "purpose", "default_rate", "Default Rate by Purpose"),
        _bar("Default Rate by Term", "Risk by Term", "term_months", "default_rate", "Default Rate by Term"),
        _bar("Default Rate by Income", "Risk by Income", "income_bucket", "default_rate", "Default Rate by Income Bucket"),
        _bar("Default Rate by DTI", "Risk by DTI", "dti_bucket", "default_rate", "Default Rate by DTI Bucket"),
        _bar("Exposure by Grade", "Risk by Grade", "grade", "funded_amount", "Funded Exposure by Grade", "SUM"),
        _line("Vintage Curves", "Vintage Curves", "loan_age_months", "cumulative_default_rate", "vintage", "Cumulative Default Rate by Loan Age"),
        _line("Cumulative Loss Rate", "Vintage Curves", "loan_age_months", "cumulative_loss_rate", "vintage", "Cumulative Loss Rate by Loan Age"),
        _bar("Expected Loss by State", "Expected Loss by State", "addr_state", "expected_loss", "Expected Loss by State", "SUM"),
        _bar("Expected Loss by Vintage", "Expected Loss by Vintage", "vintage", "expected_loss", "Expected Loss by Vintage", "SUM"),
        _scatter(
            "PD Exposure Matrix",
            "Concentration by Grade",
            "funded_amount",
            "default_rate",
            "concentration_quadrant",
            "PD Proxy vs Exposure by Grade",
        ),
        _bar("Risk Segmentation Exposure", "Risk Segmentation", "segment", "exposure", "Exposure by Risk Segment", "SUM"),
        _bar("Predicted PD Distribution", "Model Predictions", "risk_band", "predicted_pd", "Average Predicted PD by Risk Band"),
        _bar("Actual Default by Risk Band", "Model Predictions", "risk_band", "actual_default", "Actual Default Rate by Risk Band"),
        _line("Calibration Curve", "Calibration Curve", "mean_predicted_pd", "observed_default_rate", None, "Calibration: Predicted vs Observed Default Rate"),
        _line("Precision Recall Curve", "PR Curve", "recall", "precision", None, "Precision-Recall Curve"),
        _bar("Feature Importance", "Feature Importance", "feature", "importance_mean", "Permutation Importance (PR-AUC)", "SUM"),
        _bar("Risk Deciles", "Risk Deciles", "decile", "actual_default_rate", "Actual Default Rate by Predicted PD Decile"),
        _line("Threshold Analysis", "Threshold Analysis", "threshold", "precision", None, "Threshold vs Precision"),
        {
            "name": "Recommendations Table",
            "datasource": "Recommendations",
            "mark_type": "text",
            "rows": ["priority", "owner"],
            "columns": ["recommendation"],
            "title": "Priority Recommendations",
        },
    ]

    width = DASH_WIDTH
    dashboards = [
        {
            "name": "1 Executive Risk Overview",
            "title": "Executive Risk Overview",
            "width": width,
            "height": 1020,
            "zones": [
                _header_zone(
                    "Credit Risk & Loan Default Analysis  ·  Executive Risk Overview",
                    "Book size, matured default rate, and where expected loss is concentrated",
                    width,
                ),
                *_kpi_zones(kpi, y=72, width=width),
                _insight_zone("executive", width, y=168),
                *_chart_pair("Portfolio Volume Trend", "Funded Amount Trend", y=288, width=width),
                *_chart_pair("Default Rate by Vintage", "Expected Loss by Grade", y=536, width=width),
                *_chart_pair("Risk Concentration Matrix", "Top Purpose Expected Loss", y=784, width=width),
                _footer_zone(width, 1020),
            ],
        },
        {
            "name": "2 Credit Risk Segmentation",
            "title": "Credit Risk Segmentation",
            "width": width,
            "height": 1020,
            "zones": [
                _header_zone(
                    "Credit Risk & Loan Default Analysis  ·  Credit Risk Segmentation",
                    "Which grades, purposes, terms, incomes and DTI bands drive observed default",
                    width,
                ),
                _insight_zone("segmentation", width, y=72),
                *_chart_pair("Default Rate by Grade", "Default Rate by Purpose", y=192, width=width),
                *_chart_triple(
                    ["Default Rate by Term", "Default Rate by Income", "Default Rate by DTI"],
                    y=440,
                    width=width,
                ),
                *_chart_pair("Exposure by Grade", "Expected Loss by Grade", y=672, width=width, height=316),
                _footer_zone(width, 1020),
            ],
        },
        {
            "name": "3 Vintage Performance",
            "title": "Vintage Performance",
            "width": width,
            "height": 960,
            "zones": [
                _header_zone(
                    "Credit Risk & Loan Default Analysis  ·  Vintage Performance",
                    "Which vintages are underperforming and when default risk emerges",
                    width,
                ),
                _insight_zone("vintage", width, y=72),
                _chart_full("Vintage Curves", y=192, width=width, height=356),
                _chart_full("Cumulative Loss Rate", y=560, width=width, height=356),
                _footer_zone(width, 960),
            ],
        },
        {
            "name": "4 Expected Loss and Concentration",
            "title": "Expected Loss and Concentration",
            "width": width,
            "height": 1020,
            "zones": [
                _header_zone(
                    "Credit Risk & Loan Default Analysis  ·  Expected Loss and Concentration",
                    "Where PD, exposure and expected loss concentrate — and where to focus first",
                    width,
                ),
                _insight_zone("expected_loss", width, y=72),
                *_chart_pair("Expected Loss by Grade", "Expected Loss by State", y=192, width=width),
                *_chart_pair("Expected Loss by Vintage", "PD Exposure Matrix", y=440, width=width),
                _chart_full("Risk Segmentation Exposure", y=688, width=width, height=300),
                _footer_zone(width, 1020),
            ],
        },
        {
            "name": "5 Default Probability Model",
            "title": "Default Probability Model",
            "width": width,
            "height": 1020,
            "zones": [
                _header_zone(
                    "Credit Risk & Loan Default Analysis  ·  Default Probability Model",
                    "Can origination-time information rank higher-risk loans, and are the probabilities usable?",
                    width,
                ),
                _insight_zone("model", width, y=72),
                *_chart_pair("Predicted PD Distribution", "Actual Default by Risk Band", y=192, width=width),
                *_chart_pair("Calibration Curve", "Precision Recall Curve", y=440, width=width),
                *_chart_pair("Feature Importance", "Risk Deciles", y=688, width=width, height=300),
                _footer_zone(width, 1020),
            ],
        },
        {
            "name": "6 Decision and Recommendations",
            "title": "Decision and Recommendations",
            "width": width,
            "height": 960,
            "zones": [
                _header_zone(
                    "Credit Risk & Loan Default Analysis  ·  Decision and Recommendations",
                    "What should happen next, who owns it, and how progress will be measured",
                    width,
                ),
                _insight_zone("decisions", width, y=72),
                _chart_full("Recommendations Table", y=192, width=width, height=340),
                *_chart_pair(
                    "Risk Segmentation Exposure",
                    "Expected Loss by Grade",
                    y=544,
                    width=width,
                    height=384,
                ),
                _footer_zone(width, 960),
            ],
        },
    ]

    return {"datasources": datasources, "worksheets": worksheets, "dashboards": dashboards}


def build_single_dashboard_specs() -> dict[str, dict]:
    master = build_master_workbook_spec()
    mapping = {
        "dashboard_01_executive_risk_overview.twb": "1 Executive Risk Overview",
        "dashboard_02_credit_risk_segmentation.twb": "2 Credit Risk Segmentation",
        "dashboard_03_vintage_performance.twb": "3 Vintage Performance",
        "dashboard_04_expected_loss_concentration.twb": "4 Expected Loss and Concentration",
        "dashboard_05_default_probability_model.twb": "5 Default Probability Model",
        "dashboard_06_decision_recommendations.twb": "6 Decision and Recommendations",
    }
    specs: dict[str, dict] = {}
    for filename, dash_name in mapping.items():
        dashboard = next(d for d in master["dashboards"] if d["name"] == dash_name)
        worksheet_names = {zone["worksheet"] for zone in dashboard["zones"] if "worksheet" in zone}
        used_datasources = {
            ws["datasource"] for ws in master["worksheets"] if ws["name"] in worksheet_names
        }
        specs[filename] = {
            "datasources": [ds for ds in master["datasources"] if ds["caption"] in used_datasources],
            "worksheets": [ws for ws in master["worksheets"] if ws["name"] in worksheet_names],
            "dashboards": [dashboard],
        }
    return specs


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    digest = hashlib.md5(value.encode("utf-8")).hexdigest()[:8]
    return f"{slug}_{digest}"


def _ds_name(caption: str) -> str:
    return f"federated.{_slug(caption)}"


def _conn_name(csv_name: str) -> str:
    return f"textscan.{_slug(csv_name)}"


def _column_role_type(col: dict) -> tuple[str, str]:
    if col["role"] == "dimension":
        if col["datatype"] in {"integer", "real"}:
            return "dimension", "ordinal"
        return "dimension", "nominal"
    return "measure", "quantitative"


def _parse_shelf_token(token: str) -> tuple[str, str]:
    match = re.fullmatch(r"(SUM|AVG|COUNT|CNT|MIN|MAX)\((.+)\)", token, flags=re.I)
    if match:
        return match.group(1).upper().replace("COUNT", "CNT"), match.group(2)
    return "NONE", token


def _derivation_name(agg: str, field: str, role: str, datatype: str = "string") -> str:
    if agg == "NONE":
        if role == "measure":
            suffix = "qk"
        elif datatype in {"integer", "real"}:
            suffix = "ok"
        else:
            suffix = "nk"
        return f"[none:{field}:{suffix}]"
    agg_key = {"SUM": "sum", "AVG": "avg", "CNT": "cnt", "MIN": "min", "MAX": "max"}[agg]
    return f"[{agg_key}:{field}:qk]"


def _column_instance_attrs(agg: str, field: str, role: str, datatype: str) -> dict[str, str]:
    derivation = {
        "NONE": "None",
        "SUM": "Sum",
        "AVG": "Avg",
        "CNT": "Count",
        "MIN": "Min",
        "MAX": "Max",
    }[agg]
    inst_type = "nominal"
    if agg != "NONE":
        inst_type = "quantitative"
    elif role == "dimension" and datatype in {"integer", "real"}:
        inst_type = "ordinal"
    elif role == "measure":
        inst_type = "quantitative"
    return {
        "column": f"[{field}]",
        "derivation": derivation,
        "name": _derivation_name(agg, field, role, datatype),
        "pivot": "key",
        "type": inst_type,
    }


def _csv_stem(csv_name: str) -> str:
    return Path(csv_name).stem


def _relation_name(csv_name: str) -> str:
    return f"{_csv_stem(csv_name)}#csv"


def _remote_type(datatype: str) -> str:
    return {"integer": "20", "real": "5", "boolean": "11"}.get(datatype, "129")


def _add_column_element(parent, col: dict) -> None:
    role, col_type = _column_role_type(col)
    attrib = {
        "caption": col["caption"].replace("_", " ").title(),
        "datatype": col["datatype"],
        "name": f"[{col['caption']}]",
        "role": role,
        "type": col_type,
    }
    if role == "measure":
        attrib["aggregation"] = "Sum"
    etree.SubElement(parent, "column", attrib=attrib)


def _build_datasource(ds: dict) -> etree._Element:
    caption = ds["caption"]
    csv_name = ds["csv_name"]
    rel_name = _relation_name(csv_name)
    ds_el = etree.Element(
        "datasource",
        caption=caption,
        inline="true",
        name=_ds_name(caption),
        version=TABLEAU_XML_VERSION,
    )
    connection = etree.SubElement(ds_el, "connection", attrib={"class": "federated"})
    named_connections = etree.SubElement(connection, "named-connections")
    named = etree.SubElement(
        named_connections,
        "named-connection",
        name=_conn_name(csv_name),
    )
    etree.SubElement(
        named,
        "connection",
        attrib={
            "auto-extract": "yes",
            "character-set": "UTF-8",
            "class": "textscan",
            "directory": ds["directory"],
            "driver": "",
            "filename": csv_name,
            "force-character-set": "no",
            "force-header": "no",
            "force-separator": "no",
            "header": "yes",
            "separator": ",",
            "text-qualifier": '"',
        },
    )
    relation = etree.SubElement(
        connection,
        "relation",
        attrib={
            "connection": _conn_name(csv_name),
            "name": rel_name,
            "table": f"[{rel_name}]",
            "type": "table",
        },
    )
    columns_el = etree.SubElement(
        relation,
        "columns",
        attrib={
            "character-set": "UTF-8",
            "header": "yes",
            "locale": "en_US",
            "separator": ",",
            "text-qualifier": '"',
        },
    )
    for index, col in enumerate(ds["columns"]):
        etree.SubElement(
            columns_el,
            "column",
            attrib={"datatype": col["datatype"], "name": col["caption"], "ordinal": str(index)},
        )
    etree.SubElement(connection, "refresh", attrib={"increment-key": "", "incremental-updates": "false"})
    metadata = etree.SubElement(connection, "metadata-records")
    for index, col in enumerate(ds["columns"]):
        record = etree.SubElement(metadata, "metadata-record", attrib={"class": "column"})
        etree.SubElement(record, "remote-name").text = col["caption"]
        etree.SubElement(record, "remote-type").text = _remote_type(col["datatype"])
        etree.SubElement(record, "local-name").text = f"[{col['caption']}]"
        etree.SubElement(record, "parent-name").text = f"[{rel_name}]"
        etree.SubElement(record, "remote-alias").text = col["caption"]
        etree.SubElement(record, "ordinal").text = str(index)
        etree.SubElement(record, "local-type").text = col["datatype"]
        etree.SubElement(record, "aggregation").text = "Sum" if col["role"] == "measure" else "Count"
        etree.SubElement(record, "contains-null").text = "true"
    cols = etree.SubElement(connection, "cols")
    for col in ds["columns"]:
        etree.SubElement(
            cols,
            "map",
            key=f"[{col['caption']}]",
            value=f"[{rel_name}].[{col['caption']}]",
        )
    etree.SubElement(ds_el, "aliases", enabled="yes")
    for col in ds["columns"]:
        _add_column_element(ds_el, col)
    return ds_el


def _field_lookup(ds: dict) -> dict[str, dict]:
    return {col["caption"]: col for col in ds["columns"]}


def _shelf_ref(ds_caption: str, token: str, lookup: dict[str, dict]) -> str:
    agg, field = _parse_shelf_token(token)
    col = lookup[field]
    role, _ = _column_role_type(col)
    if agg == "NONE" and role == "measure":
        agg = "SUM"
        role = "measure"
    inst = _derivation_name(agg, field, role, col["datatype"])
    return f"[{_ds_name(ds_caption)}].{inst}"


def _build_worksheet(ws: dict, ds_by_caption: dict[str, dict]) -> etree._Element:
    ds = ds_by_caption[ws["datasource"]]
    lookup = _field_lookup(ds)
    ds_name = _ds_name(ds["caption"])
    worksheet = etree.Element("worksheet", name=ws["name"])
    layout_options = etree.SubElement(worksheet, "layout-options")
    title = etree.SubElement(layout_options, "title")
    formatted = etree.SubElement(title, "formatted-text")
    run = etree.SubElement(
        formatted,
        "run",
        attrib={"bold": "true", "fontsize": "12", "fontcolor": NAVY, "fontname": FONT_MED},
    )
    run.text = ws.get("title") or ws["name"]

    table = etree.SubElement(worksheet, "table")
    view = etree.SubElement(table, "view")
    datasources = etree.SubElement(view, "datasources")
    etree.SubElement(datasources, "datasource", caption=ds["caption"], name=ds_name)
    deps = etree.SubElement(view, "datasource-dependencies", datasource=ds_name)

    seen_columns: set[str] = set()
    seen_instances: set[str] = set()
    tokens = list(ws.get("rows", [])) + list(ws.get("columns", [])) + list(ws.get("color", []))
    for token in tokens:
        agg, field = _parse_shelf_token(token)
        col = lookup[field]
        role, _ = _column_role_type(col)
        if agg == "NONE" and role == "measure":
            agg = "SUM"
        if field not in seen_columns:
            _add_column_element(deps, col)
            seen_columns.add(field)
        inst_name = _column_instance_attrs(agg, field, role, col["datatype"])["name"]
        if inst_name not in seen_instances:
            etree.SubElement(deps, "column-instance", attrib=_column_instance_attrs(agg, field, role, col["datatype"]))
            seen_instances.add(inst_name)

    etree.SubElement(view, "aggregation", value="true")
    style = etree.SubElement(table, "style")
    sheet_rule = etree.SubElement(style, "style-rule", element="worksheet")
    etree.SubElement(sheet_rule, "format", attr="font-size", value="11")
    etree.SubElement(sheet_rule, "format", attr="font-family", value=FONT)
    etree.SubElement(sheet_rule, "format", attr="color", value=INK)
    etree.SubElement(sheet_rule, "format", attr="display-field-labels", scope="rows", value="false")
    header_rule = etree.SubElement(style, "style-rule", element="header")
    etree.SubElement(header_rule, "format", attr="font-size", value="10")
    etree.SubElement(header_rule, "format", attr="color", value=MUTED)
    etree.SubElement(header_rule, "format", attr="font-family", value=FONT)
    axis_rule = etree.SubElement(style, "style-rule", element="axis")
    etree.SubElement(axis_rule, "format", attr="font-size", value="9")
    etree.SubElement(axis_rule, "format", attr="color", value=MUTED)
    mark_rule = etree.SubElement(style, "style-rule", element="mark")
    if not ws.get("color"):
        etree.SubElement(mark_rule, "format", attr="mark-color", value=NAVY_MID)
    etree.SubElement(mark_rule, "format", attr="mark-labels-cull", value="true")
    cell_rule = etree.SubElement(style, "style-rule", element="cell")
    formats_added = False
    for token in list(ws.get("rows", [])) + list(ws.get("columns", [])):
        _agg, field = _parse_shelf_token(token)
        number_format = _axis_format(field)
        if number_format:
            etree.SubElement(
                cell_rule,
                "format",
                attr="text-format",
                field=_shelf_ref(ds["caption"], token, lookup),
                value=number_format,
            )
            formats_added = True
    if not formats_added:
        style.remove(cell_rule)
    panes = etree.SubElement(table, "panes")
    pane = etree.SubElement(panes, "pane")
    pane_view = etree.SubElement(pane, "view")
    etree.SubElement(pane_view, "breakdown", value="auto")
    etree.SubElement(pane, "mark", attrib={"class": MARK_CLASS.get(ws.get("mark_type", "automatic"), "Automatic")})
    encodings = etree.SubElement(pane, "encodings")
    for color_field in ws.get("color", []):
        etree.SubElement(encodings, "color", column=_shelf_ref(ds["caption"], color_field, lookup))
    if ws.get("mark_type") == "text":
        for token in ws.get("columns", []):
            etree.SubElement(encodings, "text", column=_shelf_ref(ds["caption"], token, lookup))
    if not list(encodings):
        pane.remove(encodings)

    rows = " / ".join(_shelf_ref(ds["caption"], token, lookup) for token in ws.get("rows", []))
    cols = " / ".join(_shelf_ref(ds["caption"], token, lookup) for token in ws.get("columns", []))
    etree.SubElement(table, "rows").text = rows
    etree.SubElement(table, "cols").text = cols
    return worksheet


def _axis_format(field: str) -> str | None:
    name = field.lower()
    if any(token in name for token in ("rate", "pd", "precision", "recall", "pct", "share")):
        return "p0.0%"
    if any(token in name for token in ("amount", "funded", "loss", "ead", "exposure")):
        return "$#,##0"
    if "count" in name:
        return "#,##0"
    return None


def _scaled(value: int, total: int) -> str:
    if value <= 0:
        return "0"
    return str(max(1, int(round(value / total * 100000))))


def _add_runs(parent, runs: list[dict]) -> None:
    formatted = etree.SubElement(parent, "formatted-text")
    for index, run_spec in enumerate(runs):
        attrib = {
            "fontsize": str(run_spec.get("fontsize", "11")),
            "fontname": run_spec.get("fontname", FONT),
            "fontcolor": run_spec.get("color", INK),
        }
        if run_spec.get("bold"):
            attrib["bold"] = "true"
        run = etree.SubElement(formatted, "run", attrib=attrib)
        text = run_spec.get("text") or " "
        if index and not run_spec.get("same_line"):
            text = f"\n{text}"
        run.text = text


def _apply_zone_style(zone_el, role: str, accent: str | None = None) -> None:
    style = etree.SubElement(zone_el, "zone-style")

    def fmt(attr: str, value: str) -> None:
        etree.SubElement(style, "format", attr=attr, value=value)

    if role == "header":
        fmt("background-color", NAVY)
        fmt("border-style", "none")
        fmt("padding", "14")
        fmt("margin", "0")
    elif role == "kpi":
        fmt("background-color", CARD)
        fmt("border-style", "none")
        fmt("border-style-left", "solid")
        fmt("border-width-left", "4")
        fmt("border-color-left", accent or NAVY)
        fmt("padding", "10")
        fmt("margin", "6")
    elif role == "insight":
        fmt("background-color", CARD)
        fmt("border-style", "none")
        fmt("border-style-left", "solid")
        fmt("border-width-left", "4")
        fmt("border-color-left", NAVY_MID)
        fmt("padding", "12")
        fmt("margin", "6")
    elif role == "footer":
        fmt("background-color", CANVAS)
        fmt("border-style", "none")
        fmt("padding", "2")
        fmt("margin", "0")
    else:
        fmt("background-color", CARD)
        fmt("border-color", LINE)
        fmt("border-style", "solid")
        fmt("border-width", "1")
        fmt("padding", "8")
        fmt("margin", "6")


def _formatted_text(parent, text: str, fontsize: str = "10") -> None:
    _add_runs(parent, [{"text": line if line else " ", "fontsize": fontsize} for line in text.split("\n")])


def _build_dashboard(dash: dict, worksheets: list[dict], ds_by_caption: dict[str, dict]) -> etree._Element:
    width = int(dash["width"])
    height = int(dash["height"])
    dashboard = etree.Element("dashboard", name=dash["name"])
    layout_options = etree.SubElement(dashboard, "layout-options")
    title = etree.SubElement(layout_options, "title")
    formatted = etree.SubElement(title, "formatted-text")
    run = etree.SubElement(
        formatted,
        "run",
        attrib={"fontsize": "16", "bold": "true", "fontcolor": NAVY, "fontname": FONT_MED},
    )
    run.text = dash.get("title") or dash["name"]
    etree.SubElement(dashboard, "style")
    style = dashboard.find("style")
    style_rule = etree.SubElement(style, "style-rule", element="dash-text")
    etree.SubElement(style_rule, "format", attr="wrap", value="on")
    etree.SubElement(style_rule, "format", attr="font-family", value=FONT)
    etree.SubElement(
        dashboard,
        "size",
        attrib={
            "maxheight": str(height),
            "maxwidth": str(width),
            "minheight": str(height),
            "minwidth": str(width),
        },
    )

    used_sheet_names = {zone["worksheet"] for zone in dash["zones"] if "worksheet" in zone}
    used_worksheets = [ws for ws in worksheets if ws["name"] in used_sheet_names]
    used_captions = list(dict.fromkeys(ws["datasource"] for ws in used_worksheets))
    dash_datasources = etree.SubElement(dashboard, "datasources")
    for caption in used_captions:
        ds_name = _ds_name(caption)
        etree.SubElement(dash_datasources, "datasource", caption=caption, name=ds_name)
        deps = etree.SubElement(dashboard, "datasource-dependencies", datasource=ds_name)
        ds = ds_by_caption[caption]
        for col in ds["columns"]:
            _add_column_element(deps, col)
            role, _ = _column_role_type(col)
            agg = "NONE" if role == "dimension" else "SUM"
            etree.SubElement(deps, "column-instance", attrib=_column_instance_attrs(agg, col["caption"], role, col["datatype"]))

    zones = etree.SubElement(dashboard, "zones")
    root_zone = etree.SubElement(
        zones,
        "zone",
        attrib={"h": "100000", "id": "1", "type": "layout-basic", "w": "100000", "x": "0", "y": "0"},
    )
    zone_id = 2
    for zone in dash["zones"]:
        attrib = {
            "h": _scaled(int(zone["h"]), height),
            "id": str(zone_id),
            "w": _scaled(int(zone["w"]), width),
            "x": _scaled(int(zone["x"]), width),
            "y": _scaled(int(zone["y"]), height),
        }
        zone_id += 1
        if "worksheet" in zone:
            attrib["name"] = zone["worksheet"]
            attrib["show-title"] = "true"
            child = etree.SubElement(root_zone, "zone", attrib=attrib)
        else:
            attrib["type"] = "text"
            child = etree.SubElement(root_zone, "zone", attrib=attrib)
            if zone.get("runs"):
                _add_runs(child, zone["runs"])
            else:
                _formatted_text(child, zone.get("text", ""), fontsize="11")
        _apply_zone_style(child, zone.get("role", "chart"), zone.get("accent"))
    root_style = etree.SubElement(root_zone, "zone-style")
    etree.SubElement(root_style, "format", attr="background-color", value=CANVAS)
    layouts = etree.SubElement(dashboard, "devicelayouts")
    etree.SubElement(layouts, "devicelayout", name="Desktop")
    return dashboard


def _build_windows(spec: dict) -> etree._Element:
    windows = etree.Element("windows", attrib={"source-height": "32"})
    for dash in spec["dashboards"]:
        window = etree.SubElement(
            windows,
            "window",
            attrib={"class": "dashboard", "maximized": "true", "name": dash["name"]},
        )
        viewpoints = etree.SubElement(window, "viewpoints")
        for zone in dash["zones"]:
            if "worksheet" in zone:
                viewpoint = etree.SubElement(viewpoints, "viewpoint", name=zone["worksheet"])
                etree.SubElement(viewpoint, "zoom", type="entire-view")
        etree.SubElement(window, "active", id="-1")
        etree.SubElement(window, "device-preview", selected="Desktop")
    for ws in spec["worksheets"]:
        window = etree.SubElement(windows, "window", attrib={"class": "worksheet", "name": ws["name"]})
        cards = etree.SubElement(window, "cards")
        left = etree.SubElement(cards, "edge", name="left")
        left_strip = etree.SubElement(left, "strip", size="160")
        etree.SubElement(left_strip, "card", type="pages")
        etree.SubElement(left_strip, "card", type="filters")
        etree.SubElement(left_strip, "card", type="marks")
        top = etree.SubElement(cards, "edge", name="top")
        etree.SubElement(etree.SubElement(top, "strip", size="31"), "card", type="columns")
        etree.SubElement(etree.SubElement(top, "strip", size="31"), "card", type="rows")
        etree.SubElement(etree.SubElement(top, "strip", size="31"), "card", type="title")
        etree.SubElement(window, "viewpoint")
    return windows


def write_twb(spec: dict, path: Path) -> Path:
    root = etree.Element(
        "workbook",
        nsmap={"user": USER_NS},
        attrib={
            "locale": "en_US",
            "source-build": TABLEAU_SOURCE_BUILD,
            "source-platform": "mac",
            "version": TABLEAU_XML_VERSION,
        },
    )
    document = etree.ElementTree(root)
    root.addprevious(etree.Comment(f" build {TABLEAU_SOURCE_BUILD} "))
    prefs = etree.SubElement(root, "preferences")
    etree.SubElement(prefs, "preference", name="ui.encoding.shelf.height", value="24")
    etree.SubElement(prefs, "preference", name="ui.shelf.height", value="26")
    etree.SubElement(root, "style-theme", name="smooth")
    datasources_el = etree.SubElement(root, "datasources")
    ds_by_caption = {ds["caption"]: ds for ds in spec["datasources"]}
    for ds in spec["datasources"]:
        datasources_el.append(_build_datasource(ds))
    worksheets_el = etree.SubElement(root, "worksheets")
    for ws in spec["worksheets"]:
        worksheets_el.append(_build_worksheet(ws, ds_by_caption))
    dashboards_el = etree.SubElement(root, "dashboards")
    for dash in spec["dashboards"]:
        dashboards_el.append(_build_dashboard(dash, spec["worksheets"], ds_by_caption))
    root.append(_build_windows(spec))
    path.parent.mkdir(parents=True, exist_ok=True)
    document.write(
        str(path),
        xml_declaration=True,
        encoding="utf-8",
        pretty_print=True,
    )
    text = path.read_text(encoding="utf-8")
    text = text.replace("encoding='UTF-8'", "encoding='utf-8'")
    path.write_text(text, encoding="utf-8")
    _ = escape
    return path


def build_tableau_workbooks() -> list[Path]:
    stage_supplementary_extracts()
    TABLEAU_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []

    master = build_master_workbook_spec()
    master_path = TABLEAU_OUTPUT_DIR / "Credit_Risk_Loan_Default_Analysis.twb"
    write_twb(master, master_path)
    written.append(master_path)
    logger.info("Wrote %s", master_path)

    for filename, spec in build_single_dashboard_specs().items():
        path = TABLEAU_OUTPUT_DIR / filename
        write_twb(spec, path)
        written.append(path)
        logger.info("Wrote %s", path)

    return written
