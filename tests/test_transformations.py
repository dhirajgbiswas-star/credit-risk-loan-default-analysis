import pandas as pd

from src.data.clean import clean_accepted_loans
from src.data.transform import add_risk_features, add_vintage_fields, month_diff


def test_month_diff():
    start = pd.to_datetime(["2015-01-01", "2016-12-01"])
    end = pd.to_datetime(["2016-01-01", "2017-03-01"])
    result = month_diff(pd.Series(start), pd.Series(end))
    assert result.tolist() == [12, 3]


def test_loan_age_and_vintage():
    frame = pd.DataFrame(
        {
            "issue_d_dt": pd.to_datetime(["2016-01-01", "2017-06-01"]),
            "last_pymnt_d_dt": pd.to_datetime(["2017-01-01", "2018-06-01"]),
        }
    )
    out = add_vintage_fields(frame)
    assert out.loc[0, "vintage"] == 2016
    assert out.loc[0, "loan_age_months"] == 12
    assert out.loc[1, "issue_quarter"] == "2017Q2"


def test_loan_to_income():
    frame = pd.DataFrame(
        {
            "annual_inc": [50000, 0],
            "loan_amnt": [10000, 8000],
            "installment": [300, 250],
            "dti": [12, 18],
            "int_rate": [10, 14],
        }
    )
    out = add_risk_features(frame)
    assert abs(out.loc[0, "loan_to_income"] - 0.2) < 1e-9
    assert pd.isna(out.loc[1, "loan_to_income"])


def test_clean_standardises_term_and_home_ownership():
    frame = pd.DataFrame(
        {
            "id": [1, 2],
            "loan_status": ["Fully Paid", "Charged Off"],
            "term": [" 36 months", " 60 months"],
            "home_ownership": ["NONE", "MORTGAGE"],
            "purpose": ["Debt_Consolidation", "credit_card"],
            "loan_amnt": [5000, 8000],
            "funded_amnt": [5000, 8000],
            "int_rate": [10.0, 15.0],
            "annual_inc": [60000, 70000],
            "emp_length": ["10+ years", "< 1 year"],
            "issue_d": ["Dec-2015", "Jan-2016"],
        }
    )
    out = clean_accepted_loans(frame)
    assert out["term_months"].tolist() == [36.0, 60.0]
    assert out["home_ownership"].tolist() == ["OTHER", "MORTGAGE"]
    assert out["purpose"].tolist() == ["debt_consolidation", "credit_card"]
    assert out["emp_length_years"].tolist() == [10, 0]
