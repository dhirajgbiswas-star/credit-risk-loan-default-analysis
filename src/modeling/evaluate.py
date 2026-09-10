"""Business-oriented model evaluation, threshold analysis and ranking quality."""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)

from src.config import FALSE_NEGATIVE_COST, FALSE_POSITIVE_COST


def classification_metrics(y_true, y_prob, threshold: float = 0.50) -> dict:
    y_pred = (y_prob >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    return {
        "threshold": threshold,
        "roc_auc": float(roc_auc_score(y_true, y_prob)),
        "pr_auc": float(average_precision_score(y_true, y_prob)),
        "brier": float(brier_score_loss(y_true, y_prob)),
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "f1": float(f1_score(y_true, y_pred, zero_division=0)),
        "false_positive_rate": float(fp / (fp + tn)) if (fp + tn) else np.nan,
        "true_negatives": int(tn),
        "false_positives": int(fp),
        "false_negatives": int(fn),
        "true_positives": int(tp),
        "expected_cost": float(fp * FALSE_POSITIVE_COST + fn * FALSE_NEGATIVE_COST),
    }


def threshold_table(y_true, y_prob, thresholds=None) -> pd.DataFrame:
    if thresholds is None:
        thresholds = np.round(np.linspace(0.10, 0.70, 13), 2)
    rows = [classification_metrics(y_true, y_prob, threshold=float(t)) for t in thresholds]
    return pd.DataFrame(rows)


def select_threshold(table: pd.DataFrame) -> dict:
    ranked = table.sort_values(["expected_cost", "f1"], ascending=[True, False])
    best = ranked.iloc[0].to_dict()
    best["selection_rule"] = (
        "Threshold minimises expected cost using "
        f"FP cost={FALSE_POSITIVE_COST} and FN cost={FALSE_NEGATIVE_COST}."
    )
    return best


def curve_frames(y_true, y_prob) -> dict[str, pd.DataFrame]:
    fpr, tpr, roc_thr = roc_curve(y_true, y_prob)
    precision, recall, pr_thr = precision_recall_curve(y_true, y_prob)
    roc = pd.DataFrame({"false_positive_rate": fpr, "true_positive_rate": tpr, "threshold": roc_thr})
    pr_thresholds = np.append(pr_thr, 1.0)
    pr = pd.DataFrame({"precision": precision, "recall": recall, "threshold": pr_thresholds})
    return {"roc": roc, "pr": pr}


def risk_deciles(y_true, y_prob) -> pd.DataFrame:
    frame = pd.DataFrame({"actual": y_true, "pd": y_prob})
    frame["decile"] = pd.qcut(frame["pd"], 10, labels=list(range(1, 11)), duplicates="drop")
    table = (
        frame.groupby("decile", observed=False)
        .agg(
            loan_count=("actual", "count"),
            actual_default_rate=("actual", "mean"),
            average_predicted_pd=("pd", "mean"),
        )
        .reset_index()
    )
    return table
