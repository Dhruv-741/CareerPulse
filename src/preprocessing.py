"""
CareerPulse — Preprocessing and feature engineering pipeline.

Implements leakage-safe train/val/test splitting, text vectorization,
and structured feature encoding. All transformers are fit on training data only.
"""

import logging
import re
from pathlib import Path
from typing import Tuple, List

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.compose import ColumnTransformer

logger = logging.getLogger(__name__)

RANDOM_SEED = 42
PROCESSED_DIR = Path("data/processed")

# ─── Label mapping ─────────────────────────────────────────────────────────

EXP_LEVEL_MAP = {
    "Entry level": 0,
    "Associate": 1,
    "Mid-Senior level": 2,
    "Senior": 3,
    "Director": 4,
    "Executive": 5,
}

EXP_LEVEL_LABELS = list(EXP_LEVEL_MAP.keys())

# Simplified 4-class mapping for balanced classification
EXP_4CLASS_MAP = {
    "Entry level": "Entry",
    "Associate": "Entry",
    "Mid-Senior level": "Mid",
    "Senior": "Senior",
    "Director": "Senior",
    "Executive": "Senior",
}


def clean_text(text: str) -> str:
    """Lowercase, remove HTML tags, punctuation, and extra whitespace."""
    if not isinstance(text, str):
        return ""
    text = re.sub(r"<[^>]+>", " ", text)          # strip HTML
    text = re.sub(r"[^a-zA-Z0-9\s\+\#]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text.lower()


def normalize_experience_level(level: str) -> str:
    """Standardize experience level strings."""
    if not isinstance(level, str):
        return "Mid-Senior level"
    level = level.strip().title()
    mapping = {
        "Entry Level": "Entry level",
        "Entry-Level": "Entry level",
        "Junior": "Entry level",
        "Associate": "Associate",
        "Mid Senior Level": "Mid-Senior level",
        "Mid-Senior Level": "Mid-Senior level",
        "Mid Level": "Mid-Senior level",
        "Senior Level": "Senior",
        "Senior": "Senior",
        "Lead": "Senior",
        "Director": "Director",
        "Vp": "Director",
        "Executive": "Executive",
        "C-Level": "Executive",
        "Internship": "Entry level",
    }
    return mapping.get(level, "Mid-Senior level")


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Full cleaning pipeline applied to the raw job postings dataframe.

    Steps
    -----
    1. Remove exact duplicates (on job_id and title+description hash).
    2. Standardize column names.
    3. Parse listing date; extract year and month.
    4. Normalize experience level.
    5. Handle missing values with documented strategy.
    6. Clean and normalize text fields.
    7. Parse salary to numeric.
    8. Derive useful indicator columns.
    9. Drop records with no usable target label.
    """
    logger.info("Starting cleaning. Input shape: %s", df.shape)
    df = df.copy()
    original_len = len(df)

    # 1. Remove duplicate job_ids (keep first occurrence)
    if "job_id" in df.columns:
        before = len(df)
        df = df.drop_duplicates(subset=["job_id"], keep="first")
        logger.info("Removed %d duplicate job_id rows", before - len(df))

    # Also remove near-duplicates (same title + company + description first 200 chars)
    if all(c in df.columns for c in ["title", "company_id", "description"]):
        df["_desc_key"] = df["description"].astype(str).str[:200]
        before = len(df)
        df = df.drop_duplicates(subset=["title", "company_id", "_desc_key"], keep="first")
        df = df.drop(columns=["_desc_key"])
        logger.info("Removed %d near-duplicate rows", before - len(df))

    logger.info("After dedup: %d rows (removed %d total)", len(df), original_len - len(df))

    # 2. Standardize column names
    df.columns = [c.strip().lower() for c in df.columns]

    # 3. Parse dates
    if "listed_time" in df.columns:
        df["listed_date"] = pd.to_datetime(df["listed_time"], errors="coerce")
        df["post_year"] = df["listed_date"].dt.year
        df["post_month"] = df["listed_date"].dt.month
        n_invalid_dates = df["post_year"].isna().sum()
        logger.info("Invalid/missing dates: %d rows", n_invalid_dates)
        # Fill missing year with mode
        mode_year = df["post_year"].mode()
        if len(mode_year) > 0:
            df["post_year"] = df["post_year"].fillna(mode_year[0])
            df["post_month"] = df["post_month"].fillna(1)

    # 4. Normalize experience level
    if "formatted_experience_level" in df.columns:
        missing_exp = df["formatted_experience_level"].isna().sum()
        logger.info("Missing experience level before imputation: %d (%.1f%%)",
                    missing_exp, missing_exp / len(df) * 100)
        df["formatted_experience_level"] = df["formatted_experience_level"].apply(
            normalize_experience_level
        )

    # 5. Handle missing location → fill with "Unknown"
    if "location" in df.columns:
        df["location"] = df["location"].fillna("Unknown")
        df["is_remote"] = df["location"].str.lower().str.contains(
            "remote|hybrid", na=False
        ).astype(int)

    # 6. Clean text fields
    if "title" in df.columns:
        df["title_clean"] = df["title"].apply(clean_text)

    if "description" in df.columns:
        df["description_clean"] = df["description"].apply(clean_text)
        df["description_length"] = df["description"].astype(str).str.len()

    # 7. Salary cleaning
    for sal_col in ["min_salary", "max_salary"]:
        if sal_col in df.columns:
            df[sal_col] = pd.to_numeric(df[sal_col], errors="coerce")
            # Remove implausible values (< $10k or > $5M annual)
            df.loc[df[sal_col] < 10_000, sal_col] = np.nan
            df.loc[df[sal_col] > 5_000_000, sal_col] = np.nan

    if "min_salary" in df.columns and "max_salary" in df.columns:
        df["salary_midpoint"] = (df["min_salary"] + df["max_salary"]) / 2
        df["has_salary"] = (~df["salary_midpoint"].isna()).astype(int)

    # 8. Skills count from skills_required field
    if "skills_required" in df.columns:
        df["n_skills"] = df["skills_required"].apply(
            lambda x: len(str(x).split("|")) if pd.notna(x) else 0
        )

    # 9. Work type standardization
    if "work_type" in df.columns:
        df["work_type"] = df["work_type"].fillna("Full-time")

    # Drop rows with no experience level (these cannot be used as labels)
    before = len(df)
    df = df[df["formatted_experience_level"].notna()].copy()
    logger.info("Dropped %d rows with no experience level label", before - len(df))

    logger.info("Cleaning complete. Final shape: %s", df.shape)
    return df.reset_index(drop=True)


def build_combined_text_feature(df: pd.DataFrame) -> pd.Series:
    """
    Combine title and description into a single text field for TF-IDF.
    Weighting: title is repeated 3× to give it higher importance.
    """
    def _combine(row):
        title = str(row.get("title_clean", row.get("title", "")))
        desc = str(row.get("description_clean", row.get("description", "")))
        # Title repeated 3× for emphasis
        return f"{title} {title} {title} {desc}"

    return df.apply(_combine, axis=1)


def split_data(
    df: pd.DataFrame,
    test_size: float = 0.15,
    val_size: float = 0.15,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Chronological train/val/test split.

    Rationale: Job market data has temporal structure. Using a chronological
    split prevents future data from leaking into training, more closely
    reflecting real deployment conditions where the model sees new postings.

    Split proportions: 70% train / 15% val / 15% test
    The dataset is sorted by post_year and post_month first.

    Parameters
    ----------
    df : Cleaned DataFrame with post_year and post_month columns.
    test_size : Fraction of data reserved for test.
    val_size  : Fraction of data reserved for validation.

    Returns
    -------
    train, val, test DataFrames.
    """
    if "post_year" in df.columns and "post_month" in df.columns:
        df_sorted = df.sort_values(["post_year", "post_month"]).reset_index(drop=True)
        strategy = "chronological"
    else:
        df_sorted = df.sample(frac=1, random_state=RANDOM_SEED).reset_index(drop=True)
        strategy = "random (no date column found)"

    n = len(df_sorted)
    n_test = int(n * test_size)
    n_val = int(n * val_size)
    n_train = n - n_test - n_val

    train = df_sorted.iloc[:n_train].copy()
    val = df_sorted.iloc[n_train : n_train + n_val].copy()
    test = df_sorted.iloc[n_train + n_val :].copy()

    logger.info("Split strategy: %s", strategy)
    logger.info("Train: %d | Val: %d | Test: %d", len(train), len(val), len(test))
    return train, val, test


def build_tfidf_features(
    train: pd.DataFrame,
    val: pd.DataFrame,
    test: pd.DataFrame,
    max_features: int = 5000,
) -> Tuple:
    """
    Fit TF-IDF on training text only; transform val and test.
    Prevents leakage: vocabulary and IDF weights come only from train.
    """
    vectorizer = TfidfVectorizer(
        max_features=max_features,
        ngram_range=(1, 2),
        min_df=3,
        sublinear_tf=True,
        stop_words="english",
    )
    train_text = build_combined_text_feature(train)
    val_text = build_combined_text_feature(val)
    test_text = build_combined_text_feature(test)

    X_train_tfidf = vectorizer.fit_transform(train_text)
    X_val_tfidf = vectorizer.transform(val_text)
    X_test_tfidf = vectorizer.transform(test_text)

    logger.info("TF-IDF vocabulary size: %d", len(vectorizer.vocabulary_))
    return X_train_tfidf, X_val_tfidf, X_test_tfidf, vectorizer


def encode_labels(
    train: pd.DataFrame,
    val: pd.DataFrame,
    test: pd.DataFrame,
    target_col: str = "formatted_experience_level",
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, LabelEncoder]:
    """Encode the target labels using LabelEncoder fit on training data only."""
    le = LabelEncoder()
    y_train = le.fit_transform(train[target_col])
    y_val = le.transform(val[target_col])
    y_test = le.transform(test[target_col])
    logger.info("Classes: %s", list(le.classes_))
    return y_train, y_val, y_test, le


def get_structured_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extract numerical/categorical structured features to supplement TF-IDF.
    These do NOT include columns derived from or correlated with the target label
    (e.g., salary which correlates strongly with seniority).
    """
    features = pd.DataFrame()

    if "description_length" in df.columns:
        features["desc_length"] = df["description_length"]

    if "n_skills" in df.columns:
        features["n_skills"] = df["n_skills"]

    if "is_remote" in df.columns:
        features["is_remote"] = df["is_remote"]

    if "has_salary" in df.columns:
        features["has_salary"] = df["has_salary"]

    if "post_year" in df.columns:
        features["post_year"] = df["post_year"]

    if "post_month" in df.columns:
        features["post_month_sin"] = np.sin(2 * np.pi * df["post_month"] / 12)
        features["post_month_cos"] = np.cos(2 * np.pi * df["post_month"] / 12)

    # One-hot encode work_type (top categories only)
    if "work_type" in df.columns:
        top_work_types = ["Full-time", "Contract", "Internship"]
        for wt in top_work_types:
            features[f"wt_{wt.lower().replace('-', '_')}"] = (
                df["work_type"] == wt
            ).astype(int)

    return features.fillna(0)
