"""Train and compare origination-time default models."""

from __future__ import annotations

import json
import logging
from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

from src.config import (
    HGB_MAX_ITER,
    LOGREG_MAX_ITER,
    MODEL_DIR,
    RANDOM_SEED,
    RF_MAX_SAMPLES,
    TABLE_DIR,
    TARGET_COLUMN,
    TEST_SIZE,
)
from src.modeling.calibration import calibration_table
from src.modeling.evaluate import (
    classification_metrics,
    curve_frames,
    risk_deciles,
    select_threshold,
    threshold_table,
)
from src.modeling.explainability import logistic_coefficients, permutation_table, tree_feature_importance
from src.modeling.features import build_preprocessor, leakage_assessment, model_frame

logger = logging.getLogger(__name__)


def _split(frame: pd.DataFrame):
    y = frame[TARGET_COLUMN]
    x = frame.drop(columns=[TARGET_COLUMN])
    return train_test_split(
        x,
        y,
        test_size=TEST_SIZE,
        random_state=RANDOM_SEED,
        stratify=y,
    )


def _models() -> dict:
    return {
        "logistic_regression": LogisticRegression(
            class_weight="balanced",
            max_iter=LOGREG_MAX_ITER,
            solver="lbfgs",
        ),
        "random_forest": RandomForestClassifier(
            n_estimators=200,
            max_depth=12,
            min_samples_leaf=20,
            class_weight="balanced_subsample",
            n_jobs=-1,
            random_state=RANDOM_SEED,
        ),
        "hist_gradient_boosting": HistGradientBoostingClassifier(
            max_iter=HGB_MAX_ITER,
            learning_rate=0.08,
            max_depth=6,
            min_samples_leaf=50,
            class_weight="balanced",
            random_state=RANDOM_SEED,
        ),
    }


def train_and_evaluate(analytical: pd.DataFrame) -> dict:
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    TABLE_DIR.mkdir(parents=True, exist_ok=True)

    leakage = leakage_assessment()
    leakage.to_csv(TABLE_DIR / "feature_leakage_assessment.csv", index=False)

    data = model_frame(analytical)
    imbalance = {
        "default_pct": float(data[TARGET_COLUMN].mean()),
        "non_default_pct": float(1 - data[TARGET_COLUMN].mean()),
        "imbalance_ratio": float((1 - data[TARGET_COLUMN].mean()) / data[TARGET_COLUMN].mean()),
        "n_loans": int(len(data)),
    }
    pd.DataFrame([imbalance]).to_csv(TABLE_DIR / "class_imbalance.csv", index=False)

    x_train, x_test, y_train, y_test = _split(data)
    comparison_rows = []
    artefacts = {}

    for name, estimator in _models().items():
        logger.info("Training %s", name)
        x_fit, y_fit = x_train, y_train
        if name == "random_forest" and len(x_train) > RF_MAX_SAMPLES:
            x_fit = x_train.sample(n=RF_MAX_SAMPLES, random_state=RANDOM_SEED)
            y_fit = y_train.loc[x_fit.index]
            logger.info("Random Forest trained on a stratified working sample of %s loans", f"{len(x_fit):,}")

        pipe = Pipeline(
            steps=[
                ("preprocess", build_preprocessor()),
                ("model", estimator),
            ]
        )
        pipe.fit(x_fit, y_fit)
        y_prob = pipe.predict_proba(x_test)[:, 1]
        metrics = classification_metrics(y_test, y_prob, threshold=0.50)
        metrics["model"] = name
        comparison_rows.append(metrics)
        artefacts[name] = {"pipeline": pipe, "y_prob": y_prob, "metrics": metrics}
        joblib.dump(pipe, MODEL_DIR / f"{name}.joblib")

    comparison = pd.DataFrame(comparison_rows).sort_values("pr_auc", ascending=False)
    comparison.to_csv(TABLE_DIR / "model_comparison.csv", index=False)
    best_name = comparison.iloc[0]["model"]
    best = artefacts[best_name]
    logger.info("Selected %s using PR-AUC as the primary ranking metric", best_name)

    thresholds = threshold_table(y_test, best["y_prob"])
    thresholds.to_csv(TABLE_DIR / "threshold_analysis.csv", index=False)
    chosen = select_threshold(thresholds)
    pd.DataFrame([chosen]).to_csv(TABLE_DIR / "selected_threshold.csv", index=False)

    curves = curve_frames(y_test, best["y_prob"])
    curves["roc"].to_csv(TABLE_DIR / "roc_curve.csv", index=False)
    curves["pr"].to_csv(TABLE_DIR / "pr_curve.csv", index=False)
    calibration_table(y_test, best["y_prob"]).to_csv(TABLE_DIR / "calibration_curve.csv", index=False)
    deciles = risk_deciles(y_test, best["y_prob"])
    deciles.to_csv(TABLE_DIR / "risk_deciles.csv", index=False)

    feature_names = best["pipeline"].named_steps["preprocess"].get_feature_names_out()
    coefs = logistic_coefficients(artefacts["logistic_regression"]["pipeline"], feature_names)
    if not coefs.empty:
        coefs.to_csv(TABLE_DIR / "logistic_coefficients.csv", index=False)
    importances = tree_feature_importance(best["pipeline"], feature_names)
    if not importances.empty:
        importances.to_csv(TABLE_DIR / "feature_importance.csv", index=False)
    perm = permutation_table(best["pipeline"], x_test, y_test)
    perm.to_csv(TABLE_DIR / "permutation_importance.csv", index=False)

    predictions = x_test.copy()
    predictions["actual_default"] = y_test.values
    predictions["predicted_pd"] = best["y_prob"]
    predictions["risk_band"] = pd.cut(
        predictions["predicted_pd"],
        bins=[-0.01, 0.10, 0.20, 0.30, 0.45, 1.01],
        labels=["Very Low", "Low", "Medium", "High", "Very High"],
    )
    predictions.to_parquet(MODEL_DIR / "test_predictions.parquet", index=False)

    summary = {
        "best_model": best_name,
        "imbalance": imbalance,
        "comparison": comparison.to_dict(orient="records"),
        "selected_threshold": chosen,
        "test_size": int(len(y_test)),
        "selection_objective": (
            "Rank higher-risk loans with acceptable false-positive cost and reasonably calibrated probabilities. "
            "PR-AUC is the primary comparison metric because the default class is the minority outcome."
        ),
    }
    (MODEL_DIR / "training_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary
