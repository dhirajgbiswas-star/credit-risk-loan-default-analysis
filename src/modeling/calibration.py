"""Probability calibration diagnostics."""

from __future__ import annotations

import pandas as pd
from sklearn.calibration import calibration_curve


def calibration_table(y_true, y_prob, n_bins: int = 10) -> pd.DataFrame:
    fraction_pos, mean_pred = calibration_curve(y_true, y_prob, n_bins=n_bins, strategy="quantile")
    return pd.DataFrame(
        {
            "mean_predicted_pd": mean_pred,
            "observed_default_rate": fraction_pos,
        }
    )
