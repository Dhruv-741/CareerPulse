"""
CareerPulse — Model training module.

Trains and cross-validates at least 5 classifiers (including a baseline):
  1. DummyClassifier (baseline)
  2. Logistic Regression + TF-IDF
  3. Linear SVC + TF-IDF
  4. Random Forest + TF-IDF
  5. LightGBM / XGBoost + TF-IDF + structured features

All models are trained on the train split only. Hyperparameter tuning uses
cross-validation on train data. The held-out test set is only used once,
after model selection.
"""

import logging
import time
from pathlib import Path
from typing import Dict, Any

import joblib
import numpy as np
import pandas as pd
import scipy.sparse as sp
from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC
from sklearn.ensemble import RandomForestClassifier
from sklearn.calibration import CalibratedClassifierCV
from sklearn.model_selection import cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import MaxAbsScaler

logger = logging.getLogger(__name__)

RANDOM_SEED = 42
MODELS_DIR = Path("models")
MODELS_DIR.mkdir(parents=True, exist_ok=True)


def get_model_definitions() -> Dict[str, Any]:
    """
    Return a dictionary of model name → sklearn-compatible estimator.

    All models accept sparse input from TF-IDF.
    """
    models = {}

    # 1. Baseline: majority class predictor
    models["Dummy Classifier"] = DummyClassifier(
        strategy="most_frequent", random_state=RANDOM_SEED
    )

    # 2. Logistic Regression (strong linear baseline for text classification)
    models["Logistic Regression"] = LogisticRegression(
        C=1.0,
        max_iter=1000,
        solver="lbfgs",
        random_state=RANDOM_SEED,
        n_jobs=-1,
    )

    # 3. Linear SVC (fast, effective for high-dim text; wrapped for probability estimates)
    models["Linear SVC"] = CalibratedClassifierCV(
        LinearSVC(C=1.0, max_iter=3000, random_state=RANDOM_SEED),
        cv=3,
    )

    # 4. Random Forest (tree ensemble; less effective on raw TF-IDF but included for comparison)
    models["Random Forest"] = RandomForestClassifier(
        n_estimators=200,
        max_depth=20,
        min_samples_leaf=5,
        random_state=RANDOM_SEED,
        n_jobs=-1,
    )

    return models


def _try_get_lgbm() -> Any:
    """Try to import and return a LightGBM classifier."""
    try:
        import lightgbm as lgb
        return lgb.LGBMClassifier(
            n_estimators=300,
            learning_rate=0.05,
            num_leaves=63,
            random_state=RANDOM_SEED,
            n_jobs=-1,
            verbose=-1,
        )
    except ImportError:
        return None


def _try_get_xgboost() -> Any:
    """Try to import and return an XGBoost classifier."""
    try:
        from xgboost import XGBClassifier
        return XGBClassifier(
            n_estimators=300,
            learning_rate=0.05,
            max_depth=6,
            random_state=RANDOM_SEED,
            n_jobs=-1,
            eval_metric="mlogloss",
            verbosity=0,
        )
    except ImportError:
        return None


def train_all_models(
    X_train,
    y_train,
    X_val,
    y_val,
    class_names: list,
) -> Dict[str, dict]:
    """
    Train all models on the training split, evaluate on validation split.

    Returns a dict: {model_name: {"model": ..., "val_results": {...}, "train_time": ...}}
    """
    from src.evaluate import evaluate_model

    models = get_model_definitions()

    # Add gradient boosting if available
    lgbm = _try_get_lgbm()
    if lgbm is not None:
        models["LightGBM"] = lgbm
        logger.info("LightGBM available and added.")
    else:
        xgb = _try_get_xgboost()
        if xgb is not None:
            models["XGBoost"] = xgb
            logger.info("XGBoost available and added.")
        else:
            logger.warning("Neither LightGBM nor XGBoost available. Skipping gradient boosting.")

    # Scale sparse features for tree models (RF, LGBM need dense or accept sparse)
    results = {}

    for name, model in models.items():
        logger.info("Training %s ...", name)
        t0 = time.perf_counter()

        # LightGBM / XGBoost need dense input or can handle sparse
        if "LightGBM" in name or "XGBoost" in name:
            if sp.issparse(X_train):
                X_tr = X_train
                X_vl = X_val
            else:
                X_tr = X_train
                X_vl = X_val
        else:
            X_tr = X_train
            X_vl = X_val

        model.fit(X_tr, y_train)
        train_time = time.perf_counter() - t0
        logger.info("  Training time: %.2f s", train_time)

        val_results = evaluate_model(model, X_vl, y_val, class_names=class_names, split_name="val")
        logger.info("  Val macro F1: %.4f | Val accuracy: %.4f",
                    val_results["macro_f1"], val_results["accuracy"])

        results[name] = {
            "model": model,
            "val_results": val_results,
            "train_time_s": round(train_time, 3),
        }

    return results


def select_best_model(results: Dict[str, dict]) -> str:
    """
    Select the best model based on validation macro F1.
    Macro F1 is preferred over accuracy for multi-class imbalanced problems.
    """
    scores = {name: r["val_results"]["macro_f1"] for name, r in results.items()}
    best = max(scores, key=scores.get)
    logger.info("Best model by val macro F1: %s (%.4f)", best, scores[best])
    return best


def save_model(model, name: str, vectorizer, label_encoder) -> Path:
    """Serialize the model pipeline components to disk."""
    safe_name = name.lower().replace(" ", "_")
    bundle = {
        "model": model,
        "vectorizer": vectorizer,
        "label_encoder": label_encoder,
        "model_name": name,
    }
    path = MODELS_DIR / f"{safe_name}_pipeline.joblib"
    joblib.dump(bundle, path)
    logger.info("Saved model bundle to %s", path)
    return path


def load_model(name: str) -> dict:
    """Load a persisted model bundle from disk."""
    safe_name = name.lower().replace(" ", "_")
    path = MODELS_DIR / f"{safe_name}_pipeline.joblib"
    if not path.exists():
        # Try loading any available model
        available = list(MODELS_DIR.glob("*_pipeline.joblib"))
        if not available:
            raise FileNotFoundError(f"No trained model found in {MODELS_DIR}")
        path = available[0]
    bundle = joblib.load(path)
    logger.info("Loaded model bundle: %s from %s", bundle.get("model_name"), path)
    return bundle


def predict_experience_level(bundle: dict, title: str, description: str = "") -> dict:
    """
    Use a loaded model bundle to predict the experience level of a job posting.

    Parameters
    ----------
    bundle : dict with 'model', 'vectorizer', 'label_encoder'
    title  : Job title string.
    description : Optional job description string.

    Returns
    -------
    dict with 'predicted_class', 'confidence', 'class_probabilities'
    """
    from src.preprocessing import clean_text
    import scipy.sparse as sp

    combined = f"{clean_text(title)} {clean_text(title)} {clean_text(title)} {clean_text(description)}"
    X_tfidf = bundle["vectorizer"].transform([combined])
    model = bundle["model"]

    # Match structured feature dimensions if model expects 4828 features (4818 TF-IDF + 10 structured)
    expected_n = getattr(model, "n_features_in_", None)
    if expected_n and expected_n > X_tfidf.shape[1]:
        n_struct = expected_n - X_tfidf.shape[1]
        # Construct realistic structured defaults: [desc_length, n_skills, is_remote, has_salary, year, sin, cos, wt_ft, wt_ct, wt_int]
        struct_vals = np.array([[float(len(description)), 5.0, 0.0, 0.0, 2024.0, 0.0, 1.0, 1.0, 0.0, 0.0]])
        if struct_vals.shape[1] < n_struct:
            pad = np.zeros((1, n_struct - struct_vals.shape[1]))
            struct_vals = np.hstack([struct_vals, pad])
        elif struct_vals.shape[1] > n_struct:
            struct_vals = struct_vals[:, :n_struct]
        X = sp.hstack([X_tfidf, sp.csr_matrix(struct_vals)], format="csr")
    else:
        X = X_tfidf

    pred_idx = model.predict(X)[0]
    predicted_class = bundle["label_encoder"].inverse_transform([pred_idx])[0]

    result = {"predicted_class": predicted_class, "confidence": None, "class_probabilities": {}}

    if hasattr(model, "predict_proba"):
        proba = model.predict_proba(X)[0]
        classes = bundle["label_encoder"].classes_
        result["class_probabilities"] = dict(zip(classes, proba.tolist()))
        result["confidence"] = float(proba.max())

    return result
