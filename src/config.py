"""Central configuration for paths, target definitions and modelling parameters."""

from __future__ import annotations

import logging
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw" / "lending_club"
PROCESSED_DIR = DATA_DIR / "processed"
TABLEAU_DIR = PROCESSED_DIR / "tableau"
EXTERNAL_DIR = DATA_DIR / "external"
ARCHIVE_DIR = PROJECT_ROOT / "archive"

OUTPUT_DIR = PROJECT_ROOT / "outputs"
FIGURE_DIR = OUTPUT_DIR / "figures"
TABLE_DIR = OUTPUT_DIR / "tables"
REPORT_DIR = OUTPUT_DIR / "reports"
MODEL_DIR = OUTPUT_DIR / "model"

KAGGLE_DATASET = "wordsforthewise/lending-club"
ACCEPTED_FILENAME = "accepted_2007_to_2018Q4.csv"
REJECTED_FILENAME = "rejected_2007_to_2018Q4.csv"

RANDOM_SEED = 42
MIN_SEGMENT_N = 500
STATE_MIN_N = 1000
VINTAGE_MAX_AGE = 60
SNAPSHOT_DATE = "2019-03-01"

TARGET_COLUMN = "is_default"
MATURED_FLAG = "is_matured"

DEFAULT_STATUSES = (
    "Charged Off",
    "Default",
    "Does not meet the credit policy. Status:Charged Off",
)
NON_DEFAULT_STATUSES = (
    "Fully Paid",
    "Does not meet the credit policy. Status:Fully Paid",
)
EXCLUDED_STATUSES = (
    "Current",
    "Late (31-120 days)",
    "Late (16-30 days)",
    "In Grace Period",
)

LGD_BASE = 0.50
LGD_OPTIMISTIC = 0.40
LGD_ADVERSE = 0.60

TEST_SIZE = 0.20
RF_MAX_SAMPLES = 250_000
HGB_MAX_ITER = 200
LOGREG_MAX_ITER = 1000

FALSE_POSITIVE_COST = 1.0
FALSE_NEGATIVE_COST = 5.0

ANALYSIS_COLUMNS = [
    "id",
    "loan_amnt",
    "funded_amnt",
    "funded_amnt_inv",
    "term",
    "int_rate",
    "installment",
    "grade",
    "sub_grade",
    "emp_length",
    "home_ownership",
    "annual_inc",
    "verification_status",
    "issue_d",
    "loan_status",
    "purpose",
    "zip_code",
    "addr_state",
    "dti",
    "delinq_2yrs",
    "earliest_cr_line",
    "fico_range_low",
    "fico_range_high",
    "inq_last_6mths",
    "open_acc",
    "pub_rec",
    "revol_bal",
    "revol_util",
    "total_acc",
    "initial_list_status",
    "application_type",
    "pub_rec_bankruptcies",
    "mort_acc",
    "last_pymnt_d",
    "recoveries",
    "collection_recovery_fee",
    "total_pymnt",
    "out_prncp",
    "debt_settlement_flag",
]

MODEL_FEATURES = [
    "loan_amnt",
    "term_months",
    "int_rate",
    "installment",
    "grade",
    "emp_length_years",
    "home_ownership",
    "annual_inc",
    "verification_status",
    "purpose",
    "dti",
    "delinq_2yrs",
    "fico_range_low",
    "inq_last_6mths",
    "open_acc",
    "pub_rec",
    "revol_util",
    "total_acc",
    "application_type",
    "pub_rec_bankruptcies",
    "credit_history_years",
    "loan_to_income",
    "installment_to_income",
]

LEAKAGE_FEATURES = [
    "out_prncp",
    "out_prncp_inv",
    "total_pymnt",
    "total_pymnt_inv",
    "total_rec_prncp",
    "total_rec_int",
    "total_rec_late_fee",
    "recoveries",
    "collection_recovery_fee",
    "last_pymnt_d",
    "last_pymnt_amnt",
    "next_pymnt_d",
    "last_credit_pull_d",
    "last_fico_range_high",
    "last_fico_range_low",
    "hardship_flag",
    "hardship_type",
    "hardship_reason",
    "hardship_status",
    "debt_settlement_flag",
    "settlement_status",
    "settlement_amount",
    "loan_status",
]

SENSITIVE_OR_PROXY_FEATURES = [
    "addr_state",
    "zip_code",
    "emp_title",
    "title",
]


def ensure_directories() -> None:
    for path in (
        RAW_DIR,
        PROCESSED_DIR,
        TABLEAU_DIR,
        EXTERNAL_DIR,
        FIGURE_DIR,
        TABLE_DIR,
        REPORT_DIR,
        MODEL_DIR,
    ):
        path.mkdir(parents=True, exist_ok=True)


def configure_logging(level: int = logging.INFO) -> None:
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
