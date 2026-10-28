"""
CareerPulse — End-to-end training pipeline.

Run this script to:
1. Generate synthetic data (if not already present)
2. Clean and split the data
3. Build features
4. Train all models
5. Select best model on validation set
6. Evaluate on test set (once, final)
7. Save trained model, preprocessing pipeline, and results

Usage:
    python scripts/run_pipeline.py
"""

import logging
import sys
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("pipeline.log")],
)
logger = logging.getLogger("pipeline")

RANDOM_SEED = 42
np.random.seed(RANDOM_SEED)

PROCESSED_DIR = Path("data/processed")
FIGURES_DIR = Path("figures")
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
FIGURES_DIR.mkdir(parents=True, exist_ok=True)


def main():
    # ── Step 0: Generate data if needed ─────────────────────────────────────
    from scripts.generate_synthetic_data import generate_dataset

    raw_path = Path("data/raw/job_postings.csv")
    if not raw_path.exists():
        logger.info("Raw data not found. Generating synthetic dataset...")
        generate_dataset(n_records=15000)
    else:
        logger.info("Raw data found at %s", raw_path)

    # ── Step 1: Load raw data ────────────────────────────────────────────────
    from src.data_loader import load_raw_data
    jobs, companies, skills = load_raw_data()
    logger.info("Raw: %d postings, %d companies, %d skill rows", len(jobs), len(companies), len(skills))

    # ── Step 2: Clean ────────────────────────────────────────────────────────
    from src.preprocessing import clean_dataframe, split_data
    df_clean = clean_dataframe(jobs)
    logger.info("After cleaning: %d rows", len(df_clean))
    df_clean.to_csv(PROCESSED_DIR / "jobs_clean.csv", index=False)
    logger.info("Saved cleaned data.")

    # ── Step 3: Split ────────────────────────────────────────────────────────
    train, val, test = split_data(df_clean, test_size=0.15, val_size=0.15)
    logger.info("Split sizes — Train: %d | Val: %d | Test: %d", len(train), len(val), len(test))

    for name, subset in [("train", train), ("val", val), ("test", test)]:
        subset.to_csv(PROCESSED_DIR / f"{name}_set.csv", index=False)

    # ── Step 4: Build TF-IDF features ───────────────────────────────────────
    from src.preprocessing import build_tfidf_features, encode_labels, get_structured_features
    from src.feature_engineering import combine_features, build_feature_report

    TARGET_COL = "formatted_experience_level"
    y_train, y_val, y_test, label_encoder = encode_labels(train, val, test, target_col=TARGET_COL)
    class_names = list(label_encoder.classes_)
    logger.info("Classes: %s", class_names)

    X_train_tfidf, X_val_tfidf, X_test_tfidf, vectorizer = build_tfidf_features(
        train, val, test, max_features=5000
    )

    struct_train = get_structured_features(train)
    struct_val = get_structured_features(val)
    struct_test = get_structured_features(test)

    X_train = combine_features(X_train_tfidf, struct_train)
    X_val = combine_features(X_val_tfidf, struct_val)
    X_test = combine_features(X_test_tfidf, struct_test)

    feat_report = build_feature_report(X_train, X_val, X_test, y_train, y_val, y_test, class_names)
    logger.info("Feature report: %s", feat_report)
    with open(PROCESSED_DIR / "feature_report.json", "w") as f:
        json.dump(feat_report, f, indent=2)

    # ── Step 5: Train all models ─────────────────────────────────────────────
    from src.train import train_all_models, select_best_model, save_model
    from src.evaluate import (
        evaluate_model, build_results_table,
        plot_model_comparison, plot_confusion_matrix, plot_class_distribution,
    )

    all_results = train_all_models(X_train, y_train, X_val, y_val, class_names)

    # Build and save comparison table
    results_df = build_results_table(all_results)
    logger.info("\n%s", results_df[["Accuracy", "Macro F1", "Weighted F1"]].to_string())
    results_df.to_csv(PROCESSED_DIR / "model_results.csv")
    logger.info("Saved model comparison table to data/processed/model_results.csv")

    # Charts
    plot_model_comparison(results_df, save_path=FIGURES_DIR / "model_comparison.png")
    plot_class_distribution(y_train, class_names,
                            title="Training Set Class Distribution",
                            save_path=FIGURES_DIR / "class_distribution_train.png")

    # ── Step 6: Select best model ────────────────────────────────────────────
    best_name = select_best_model(all_results)
    best_model = all_results[best_name]["model"]

    # ── Step 7: Final evaluation on test set ─────────────────────────────────
    test_results = evaluate_model(best_model, X_test, y_test,
                                  class_names=class_names, split_name="test")
    logger.info(
        "FINAL TEST — Model: %s | Accuracy: %.4f | Macro F1: %.4f | ROC-AUC: %s",
        best_name, test_results["accuracy"], test_results["macro_f1"],
        str(test_results.get("roc_auc")),
    )

    plot_confusion_matrix(
        y_pred=test_results["y_pred"],
        y_true=test_results["y_true"],
        class_names=class_names,
        title=f"{best_name} — Test Set",
        save_path=FIGURES_DIR / "confusion_matrix_test.png",
    )

    # Save final test results
    test_record = {
        "best_model": best_name,
        "test_accuracy": test_results["accuracy"],
        "test_macro_f1": test_results["macro_f1"],
        "test_weighted_f1": test_results["weighted_f1"],
        "test_roc_auc": test_results.get("roc_auc"),
        "test_macro_precision": test_results["macro_precision"],
        "test_macro_recall": test_results["macro_recall"],
        "n_test_samples": len(y_test),
        "class_names": class_names,
        "random_seed": RANDOM_SEED,
        "split_proportions": {"train": 0.70, "val": 0.15, "test": 0.15},
    }
    with open(PROCESSED_DIR / "best_model_test_results.json", "w") as f:
        json.dump(test_record, f, indent=2)

    # ── Step 8: Save model ───────────────────────────────────────────────────
    from src.train import save_model
    model_path = save_model(best_model, best_name, vectorizer, label_encoder)
    logger.info("Model saved to %s", model_path)

    # ── Step 9: Smoke test — load and predict ────────────────────────────────
    from src.train import load_model, predict_experience_level
    bundle = load_model(best_name)
    test_pred = predict_experience_level(
        bundle,
        title="Senior Data Scientist",
        description="Looking for an experienced data scientist with 5+ years in ML, Python, TensorFlow.",
    )
    logger.info("Smoke test prediction: %s", test_pred)
    assert test_pred["predicted_class"] in class_names, "Prediction class not in known classes!"
    logger.info("Smoke test PASSED.")

    logger.info("\n" + "=" * 60)
    logger.info("Pipeline complete.")
    logger.info("Best model: %s", best_name)
    logger.info("Test accuracy: %.4f", test_record["test_accuracy"])
    logger.info("Test macro F1: %.4f", test_record["test_macro_f1"])
    logger.info("=" * 60)

    return test_record


if __name__ == "__main__":
    main()
