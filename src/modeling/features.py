"""Origination-time feature preparation and leakage controls."""

from __future__ import annotations

import logging

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from src.config import LEAKAGE_FEATURES, MODEL_FEATURES, SENSITIVE_OR_PROXY_FEATURES, TARGET_COLUMN

logger = logging.getLogger(__name__)

NUMERIC_FEATURES = [
    "loan_amnt",
    "term_months",
    "int_rate",
    "installment",
    "emp_length_years",
    "annual_inc",
    "dti",
    "delinq_2yrs",
    "fico_range_low",
    "inq_last_6mths",
    "open_acc",
    "pub_rec",
    "revol_util",
    "total_acc",
    "pub_rec_bankruptcies",
    "credit_history_years",
    "loan_to_income",
    "installment_to_income",
]

CATEGORICAL_FEATURES = [
    "grade",
    "home_ownership",
    "verification_status",
    "purpose",
    "application_type",
]


def leakage_assessment() -> pd.DataFrame:
    rows = []
    for feature in LEAKAGE_FEATURES:
        rows.append(
            {
                "feature": feature,
                "reason_for_leakage_risk": "Observed after origination or encodes the outcome",
                "decision_time_availability": "Not available at underwriting",
                "treatment": "Excluded from the probability-of-default model",
                "rationale": "Using post-origination payment, recovery or settlement fields would inflate model performance and would not be available when a lending decision is made.",
            }
        )
    for feature in SENSITIVE_OR_PROXY_FEATURES:
        rows.append(
            {
                "feature": feature,
                "reason_for_leakage_risk": "Sensitive attribute or potential proxy",
                "decision_time_availability": "May be known at application",
                "treatment": "Excluded from the primary model; retained for portfolio analysis only",
                "rationale": "Geographic and free-text employment fields can act as proxies and are not used to score individual applicants in this study.",
            }
        )
    return pd.DataFrame(rows)


def model_frame(frame: pd.DataFrame) -> pd.DataFrame:
    required = [col for col in MODEL_FEATURES if col in frame.columns]
    missing = [col for col in MODEL_FEATURES if col not in frame.columns]
    if missing:
        logger.warning("Model features missing from the analytical dataset: %s", missing)
    matured = frame.loc[frame["is_matured"] == True, required + [TARGET_COLUMN]].copy()  # noqa: E712
    matured = matured.loc[matured[TARGET_COLUMN].isin([0, 1])].copy()
    matured[TARGET_COLUMN] = matured[TARGET_COLUMN].astype(int)
    logger.info(
        "Model dataset: %s matured loans, default rate %.2f%%",
        f"{len(matured):,}",
        100 * matured[TARGET_COLUMN].mean(),
    )
    return matured


def build_preprocessor() -> ColumnTransformer:
    numeric = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )
    categorical = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("encoder", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
        ]
    )
    return ColumnTransformer(
        transformers=[
            ("num", numeric, [c for c in NUMERIC_FEATURES if c in MODEL_FEATURES]),
            ("cat", categorical, [c for c in CATEGORICAL_FEATURES if c in MODEL_FEATURES]),
        ]
    )
