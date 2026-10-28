"""
CareerPulse — Data loading module.

Loads and caches raw and processed datasets from the data/ directory.
"""

import json
import logging
from pathlib import Path
from typing import Optional, Tuple

import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

RAW_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")
RANDOM_SEED = 42


def load_raw_data() -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Load raw CSV files from data/raw/.

    Returns
    -------
    job_postings : pd.DataFrame
    companies    : pd.DataFrame
    skills       : pd.DataFrame
    """
    job_path = RAW_DIR / "job_postings.csv"
    company_path = RAW_DIR / "companies.csv"
    skills_path = RAW_DIR / "skills.csv"

    if not job_path.exists():
        raise FileNotFoundError(
            f"Raw data not found at {job_path}. "
            "Run 'python scripts/generate_synthetic_data.py' first."
        )

    jobs = pd.read_csv(job_path, low_memory=False)
    companies = pd.read_csv(company_path, low_memory=False)
    skills = pd.read_csv(skills_path, low_memory=False)

    logger.info("Loaded raw data: %d job postings, %d companies, %d skill rows",
                len(jobs), len(companies), len(skills))
    return jobs, companies, skills


def load_processed_data() -> Optional[pd.DataFrame]:
    """
    Load the cleaned, processed dataset from data/processed/.

    Returns None if processed data does not yet exist.
    """
    path = PROCESSED_DIR / "jobs_clean.csv"
    if not path.exists():
        logger.warning("Processed data not found at %s. Run preprocessing first.", path)
        return None
    df = pd.read_csv(path, low_memory=False)
    logger.info("Loaded processed data: %d rows", len(df))
    return df


def load_dataset_metadata() -> dict:
    """Load dataset metadata JSON."""
    meta_path = RAW_DIR / "dataset_metadata.json"
    if meta_path.exists():
        with open(meta_path) as f:
            return json.load(f)
    return {
        "source": "Unknown — metadata file missing",
        "date_coverage": "Unknown",
        "n_postings": "Unknown",
    }


def load_model_results() -> Optional[pd.DataFrame]:
    """Load saved model comparison results if available."""
    path = PROCESSED_DIR / "model_results.csv"
    if path.exists():
        return pd.read_csv(path)
    return None


def get_data_summary(jobs: pd.DataFrame) -> dict:
    """
    Return a dictionary of basic dataset summary statistics.
    These are derived from actual data, never hardcoded.
    """
    summary = {
        "total_records": len(jobs),
        "unique_companies": jobs["company_id"].nunique() if "company_id" in jobs.columns else 0,
        "unique_titles": jobs["title"].nunique() if "title" in jobs.columns else 0,
        "date_range": "N/A",
        "missing_exp_level_pct": 0.0,
    }

    if "listed_time" in jobs.columns:
        try:
            dates = pd.to_datetime(jobs["listed_time"], errors="coerce")
            valid_dates = dates.dropna()
            if len(valid_dates) > 0:
                summary["date_range"] = (
                    f"{valid_dates.min().strftime('%Y-%m-%d')} to "
                    f"{valid_dates.max().strftime('%Y-%m-%d')}"
                )
        except Exception:
            pass

    if "formatted_experience_level" in jobs.columns:
        miss_pct = jobs["formatted_experience_level"].isna().mean() * 100
        summary["missing_exp_level_pct"] = round(miss_pct, 2)

    return summary
