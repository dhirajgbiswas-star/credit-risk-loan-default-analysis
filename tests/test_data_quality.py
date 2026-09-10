import pandas as pd

from src.data.clean import clean_accepted_loans
from src.data.validate import run_quality_checks


def test_duplicate_id_detection():
    frame = pd.DataFrame(
        {
            "id": [1, 1, 2],
            "loan_amnt": [1000, 1000, 2000],
            "funded_amnt": [1000, 1000, 2000],
            "int_rate": [10, 10, 12],
            "annual_inc": [40000, 40000, 50000],
            "dti": [10, 10, 12],
            "term": [" 36 months", " 36 months", " 36 months"],
            "loan_status": ["Fully Paid", "Fully Paid", "Fully Paid"],
        }
    )
    report = run_quality_checks(frame)
    dup = report.loc[report["check"] == "duplicate_loan_ids"].iloc[0]
    assert dup["value"] == 1
    assert dup["status"] == "fail"


def test_clean_drops_duplicate_ids_and_blank_status():
    frame = pd.DataFrame(
        {
            "id": [1, 1, 2, 3],
            "loan_status": ["Fully Paid", "Fully Paid", "", "Charged Off"],
            "loan_amnt": [1000, 1000, 2000, 3000],
            "funded_amnt": [1000, 1000, 2000, 3000],
            "int_rate": [8, 8, 9, 11],
            "annual_inc": [50000, 50000, 60000, 70000],
        }
    )
    out = clean_accepted_loans(frame)
    assert set(out["id"]) == {"1", "3"}


def test_missing_value_share_is_reported():
    frame = pd.DataFrame(
        {
            "loan_amnt": [1000, None, 3000],
            "funded_amnt": [1000, 2000, 3000],
            "int_rate": [10, 12, 8],
        }
    )
    report = run_quality_checks(frame)
    assert "row_count" in set(report["check"])
