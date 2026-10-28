"""
CareerPulse — Model evaluation module.

Computes and returns all required classification metrics.
Generates confusion matrices and comparison charts.
"""

import logging
from pathlib import Path
from typing import List, Optional

import matplotlib
matplotlib.use("Agg")  # Non-interactive backend for server environments
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)

logger = logging.getLogger(__name__)
FIGURES_DIR = Path("figures")
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

PALETTE = "#1f77b4"
COLORS = ["#2196F3", "#4CAF50", "#FF9800", "#F44336", "#9C27B0", "#009688"]


def evaluate_model(
    model,
    X,
    y_true: np.ndarray,
    class_names: List[str],
    split_name: str = "val",
) -> dict:
    """
    Evaluate a fitted model on X and return a metrics dictionary.

    Metrics: accuracy, macro precision, macro recall, macro F1,
             weighted F1, per-class F1, ROC-AUC (OVR where applicable).
    """
    y_pred = model.predict(X)

    metrics = {
        "split": split_name,
        "accuracy": round(float(accuracy_score(y_true, y_pred)), 4),
        "macro_precision": round(float(precision_score(y_true, y_pred, average="macro", zero_division=0)), 4),
        "macro_recall": round(float(recall_score(y_true, y_pred, average="macro", zero_division=0)), 4),
        "macro_f1": round(float(f1_score(y_true, y_pred, average="macro", zero_division=0)), 4),
        "weighted_f1": round(float(f1_score(y_true, y_pred, average="weighted", zero_division=0)), 4),
        "y_pred": y_pred,
        "y_true": y_true,
    }

    # Per-class F1
    f1_per_class = f1_score(y_true, y_pred, average=None, zero_division=0)
    for cls, f1 in zip(class_names, f1_per_class):
        metrics[f"f1_{cls.replace(' ', '_').replace('-', '_').lower()}"] = round(float(f1), 4)

    # ROC-AUC (only if model has predict_proba)
    if hasattr(model, "predict_proba"):
        try:
            proba = model.predict_proba(X)
            n_classes = len(class_names)
            if n_classes == 2:
                auc = roc_auc_score(y_true, proba[:, 1])
            else:
                auc = roc_auc_score(y_true, proba, multi_class="ovr", average="macro")
            metrics["roc_auc"] = round(float(auc), 4)
        except Exception as e:
            logger.warning("ROC-AUC computation failed: %s", e)
            metrics["roc_auc"] = None
    else:
        metrics["roc_auc"] = None

    return metrics


def build_results_table(all_results: dict) -> pd.DataFrame:
    """
    Build a clean comparison table from all model results.
    Each row is one model, columns are key metrics.
    """
    rows = []
    for model_name, result in all_results.items():
        vr = result["val_results"]
        row = {
            "Model": model_name,
            "Accuracy": vr["accuracy"],
            "Macro Precision": vr["macro_precision"],
            "Macro Recall": vr["macro_recall"],
            "Macro F1": vr["macro_f1"],
            "Weighted F1": vr["weighted_f1"],
            "ROC-AUC (OVR)": vr.get("roc_auc", None),
            "Train Time (s)": result.get("train_time_s", None),
        }
        rows.append(row)
    df = pd.DataFrame(rows).set_index("Model")
    return df


def plot_model_comparison(results_df: pd.DataFrame, save_path: Optional[Path] = None) -> Path:
    """Bar chart comparing models on key validation metrics."""
    metrics = ["Accuracy", "Macro F1", "Weighted F1"]
    available = [m for m in metrics if m in results_df.columns]

    fig, ax = plt.subplots(figsize=(10, 5))
    x = np.arange(len(results_df))
    width = 0.25

    for i, metric in enumerate(available):
        bars = ax.bar(
            x + i * width,
            results_df[metric].values,
            width,
            label=metric,
            color=COLORS[i],
            alpha=0.85,
        )
        for bar in bars:
            h = bar.get_height()
            ax.annotate(
                f"{h:.3f}",
                xy=(bar.get_x() + bar.get_width() / 2, h),
                xytext=(0, 3),
                textcoords="offset points",
                ha="center",
                va="bottom",
                fontsize=7.5,
            )

    ax.set_xticks(x + width)
    ax.set_xticklabels(results_df.index, rotation=15, ha="right", fontsize=9)
    ax.set_ylim(0, 1.12)
    ax.set_ylabel("Score")
    ax.set_title("Model Comparison — Validation Set Performance", fontsize=12, fontweight="bold")
    ax.legend(loc="upper right", fontsize=8)
    ax.grid(axis="y", alpha=0.3)
    plt.tight_layout()

    path = save_path or FIGURES_DIR / "model_comparison.png"
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    logger.info("Saved model comparison chart to %s", path)
    return path


def plot_confusion_matrix(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    class_names: List[str],
    title: str = "Confusion Matrix",
    save_path: Optional[Path] = None,
) -> Path:
    """Plot and save a normalized confusion matrix."""
    cm = confusion_matrix(y_true, y_pred)
    cm_norm = cm.astype(float) / cm.sum(axis=1, keepdims=True)

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    for ax, data, fmt, subtitle in zip(
        axes,
        [cm, cm_norm],
        ["d", ".2f"],
        ["Count", "Normalized (row %)"],
    ):
        sns.heatmap(
            data,
            annot=True,
            fmt=fmt,
            cmap="Blues",
            xticklabels=class_names,
            yticklabels=class_names,
            ax=ax,
            linewidths=0.5,
            cbar_kws={"shrink": 0.8},
        )
        ax.set_xlabel("Predicted Label", fontsize=10)
        ax.set_ylabel("True Label", fontsize=10)
        ax.set_title(f"{title} — {subtitle}", fontsize=11)
        ax.tick_params(axis="x", rotation=30, labelsize=8)
        ax.tick_params(axis="y", rotation=0, labelsize=8)

    plt.tight_layout()
    path = save_path or FIGURES_DIR / "confusion_matrix.png"
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    logger.info("Saved confusion matrix to %s", path)
    return path


def plot_class_distribution(y: np.ndarray, class_names: List[str], title: str = "Class Distribution", save_path: Optional[Path] = None) -> Path:
    """Bar chart showing class distribution."""
    counts = pd.Series(y).value_counts().sort_index()
    labels = [class_names[i] for i in counts.index]

    fig, ax = plt.subplots(figsize=(8, 4))
    bars = ax.bar(labels, counts.values, color=COLORS[:len(labels)], alpha=0.85)
    for bar in bars:
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2, h + 10, f"{int(h):,}", ha="center", fontsize=9)
    ax.set_xlabel("Experience Level")
    ax.set_ylabel("Count")
    ax.set_title(title, fontsize=12, fontweight="bold")
    plt.xticks(rotation=20, ha="right")
    plt.tight_layout()

    path = save_path or FIGURES_DIR / "class_distribution.png"
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path
