"""Model interpretability helpers. Associations are predictive, not causal."""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.inspection import permutation_importance


def logistic_coefficients(pipeline, feature_names: list[str] | None = None) -> pd.DataFrame:
    model = pipeline.named_steps["model"]
    if not hasattr(model, "coef_"):
        return pd.DataFrame()
    names = feature_names
    if names is None:
        names = pipeline.named_steps["preprocess"].get_feature_names_out()
    coef = model.coef_.ravel()
    table = pd.DataFrame(
        {
            "feature": names,
            "coefficient": coef,
            "abs_coefficient": np.abs(coef),
            "direction": np.where(coef > 0, "associated with higher predicted default risk", "associated with lower predicted default risk"),
        }
    )
    return table.sort_values("abs_coefficient", ascending=False)


def tree_feature_importance(pipeline, feature_names: list[str] | None = None) -> pd.DataFrame:
    model = pipeline.named_steps["model"]
    if not hasattr(model, "feature_importances_"):
        return pd.DataFrame()
    names = feature_names
    if names is None:
        names = pipeline.named_steps["preprocess"].get_feature_names_out()
    table = pd.DataFrame({"feature": names, "importance": model.feature_importances_})
    return table.sort_values("importance", ascending=False)


def permutation_table(pipeline, x, y, n_repeats: int = 5, max_samples: int = 25000) -> pd.DataFrame:
    if len(x) > max_samples:
        x = x.sample(n=max_samples, random_state=42)
        y = y.loc[x.index]
    result = permutation_importance(
        pipeline,
        x,
        y,
        n_repeats=n_repeats,
        random_state=42,
        scoring="average_precision",
    )
    return pd.DataFrame(
        {
            "feature": x.columns,
            "importance_mean": result.importances_mean,
            "importance_std": result.importances_std,
        }
    ).sort_values("importance_mean", ascending=False)
