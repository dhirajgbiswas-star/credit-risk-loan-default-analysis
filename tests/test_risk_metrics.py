import pandas as pd

from src.data.clean import assign_target
from src.analysis.risk import risk_by_segment


def test_target_creation_excludes_open_loans():
    frame = pd.DataFrame(
        {
            "loan_status": [
                "Fully Paid",
                "Charged Off",
                "Current",
                "Default",
                "Late (31-120 days)",
                "Does not meet the credit policy. Status:Charged Off",
            ]
        }
    )
    out = assign_target(frame)
    assert out.loc[0, "is_default"] == 0
    assert out.loc[1, "is_default"] == 1
    assert pd.isna(out.loc[2, "is_default"])
    assert out.loc[3, "is_default"] == 1
    assert pd.isna(out.loc[4, "is_default"])
    assert out.loc[5, "is_default"] == 1
    assert out["is_matured"].tolist() == [True, True, False, True, False, True]


def test_default_rate_uses_matured_loans_only():
    frame = pd.DataFrame(
        {
            "id": [1, 2, 3, 4],
            "loan_status": ["Fully Paid", "Charged Off", "Current", "Fully Paid"],
            "funded_amnt": [1000, 2000, 3000, 4000],
            "loan_amnt": [1000, 2000, 3000, 4000],
            "int_rate": [8, 18, 12, 10],
            "dti": [10, 20, 15, 12],
            "grade": ["A", "A", "A", "A"],
            "is_charged_off": [0, 1, 0, 0],
        }
    )
    frame = assign_target(frame)
    table = risk_by_segment(frame, "grade", min_n=1)
    assert table.iloc[0]["loan_count"] == 3
    assert table.iloc[0]["default_rate"] == 1 / 3
