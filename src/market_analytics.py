"""
CareerPulse — Market analytics module.

Provides aggregation functions for job market intelligence:
- Posting trends by year, domain, company
- Top skills per domain/role
- Experience level distributions
- Salary summaries

All results are derived from the actual dataset — no hardcoded values.
"""

import logging
from typing import Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def get_postings_by_year(df: pd.DataFrame) -> pd.DataFrame:
    """Return posting counts by year. Data only; not actual hires."""
    if "post_year" not in df.columns:
        return pd.DataFrame()
    return (
        df.groupby("post_year")
        .size()
        .reset_index(name="posting_count")
        .sort_values("post_year")
    )


def get_postings_by_year_domain(df: pd.DataFrame) -> pd.DataFrame:
    """Return posting counts by year and domain."""
    if "post_year" not in df.columns or "domain" not in df.columns:
        return pd.DataFrame()
    return (
        df.groupby(["post_year", "domain"])
        .size()
        .reset_index(name="posting_count")
        .sort_values(["post_year", "posting_count"], ascending=[True, False])
    )


def get_top_companies(
    df: pd.DataFrame,
    companies_df: pd.DataFrame,
    domain: Optional[str] = None,
    role: Optional[str] = None,
    top_n: int = 15,
) -> pd.DataFrame:
    """
    Return companies with the most job postings for given filters.

    Note: Posting counts are a proxy for observed recruitment activity,
    not confirmed employee hires. Dataset covers 2023-2024 only.
    """
    filtered = df.copy()
    if domain and domain != "All":
        filtered = filtered[filtered["domain"] == domain]
    if role and role != "All":
        filtered = filtered[filtered["title"].str.contains(role, case=False, na=False)]

    if len(filtered) == 0:
        return pd.DataFrame()

    company_counts = (
        filtered.groupby("company_id")
        .size()
        .reset_index(name="posting_count")
        .sort_values("posting_count", ascending=False)
        .head(top_n)
    )

    # Merge with company names
    if "company_id" in companies_df.columns and "name" in companies_df.columns:
        merged = company_counts.merge(
            companies_df[["company_id", "name", "industry", "headquarters"]],
            on="company_id",
            how="left",
        )
    else:
        merged = company_counts.copy()
        merged["name"] = "Company " + merged["company_id"].astype(str)

    return merged


def get_top_skills(
    df: pd.DataFrame,
    domain: Optional[str] = None,
    role: Optional[str] = None,
    top_n: int = 20,
) -> pd.DataFrame:
    """
    Extract and rank the most frequently requested skills.
    Skills are parsed from the pipe-delimited 'skills_required' column.
    """
    filtered = df.copy()
    if domain and domain != "All":
        filtered = filtered[filtered["domain"] == domain]
    if role and role != "All":
        filtered = filtered[filtered["title"].str.contains(role, case=False, na=False)]

    if len(filtered) == 0 or "skills_required" not in filtered.columns:
        return pd.DataFrame()

    skill_series = (
        filtered["skills_required"]
        .dropna()
        .str.split("|")
        .explode()
        .str.strip()
        .str.title()
    )
    skill_counts = (
        skill_series[skill_series != ""]
        .value_counts()
        .head(top_n)
        .reset_index()
    )
    skill_counts.columns = ["skill", "count"]
    skill_counts["pct_of_postings"] = (
        skill_counts["count"] / len(filtered) * 100
    ).round(1)
    return skill_counts


def get_experience_distribution(
    df: pd.DataFrame,
    domain: Optional[str] = None,
) -> pd.DataFrame:
    """Return experience level distribution for the given domain."""
    filtered = df.copy()
    if domain and domain != "All":
        filtered = filtered[filtered["domain"] == domain]

    if "formatted_experience_level" not in filtered.columns:
        return pd.DataFrame()

    dist = (
        filtered["formatted_experience_level"]
        .value_counts()
        .reset_index()
    )
    dist.columns = ["experience_level", "count"]
    dist["pct"] = (dist["count"] / dist["count"].sum() * 100).round(1)
    return dist


def get_salary_stats(df: pd.DataFrame, domain: Optional[str] = None) -> dict:
    """
    Return salary statistics for postings that have salary data.
    Clearly notes that not all postings include salary information.
    """
    filtered = df.copy()
    if domain and domain != "All":
        filtered = filtered[filtered["domain"] == domain]

    if "salary_midpoint" not in filtered.columns:
        return {"available": False, "reason": "No salary data in dataset"}

    sal = filtered["salary_midpoint"].dropna()
    if len(sal) < 10:
        return {"available": False, "reason": f"Insufficient salary data (n={len(sal)})"}

    return {
        "available": True,
        "n_with_salary": int(len(sal)),
        "pct_with_salary": round(len(sal) / len(filtered) * 100, 1),
        "median_usd": int(sal.median()),
        "mean_usd": int(sal.mean()),
        "p25_usd": int(sal.quantile(0.25)),
        "p75_usd": int(sal.quantile(0.75)),
        "min_usd": int(sal.min()),
        "max_usd": int(sal.max()),
        "currency": "USD",
        "period": "Annual",
    }


def get_role_trends(
    df: pd.DataFrame,
    domain: Optional[str] = None,
    top_n_roles: int = 8,
) -> pd.DataFrame:
    """Return posting count by top roles over years."""
    filtered = df.copy()
    if domain and domain != "All":
        filtered = filtered[filtered["domain"] == domain]

    if "post_year" not in filtered.columns or "title" not in filtered.columns:
        return pd.DataFrame()

    # Get top roles by overall count
    top_roles = (
        filtered["title"].value_counts().head(top_n_roles).index.tolist()
    )
    filtered_top = filtered[filtered["title"].isin(top_roles)]

    trend = (
        filtered_top.groupby(["post_year", "title"])
        .size()
        .reset_index(name="posting_count")
    )
    return trend


def get_location_distribution(
    df: pd.DataFrame,
    domain: Optional[str] = None,
    top_n: int = 15,
) -> pd.DataFrame:
    """Return posting distribution by location."""
    filtered = df.copy()
    if domain and domain != "All":
        filtered = filtered[filtered["domain"] == domain]

    if "location" not in filtered.columns:
        return pd.DataFrame()

    loc = (
        filtered["location"]
        .str.replace(r"^Hybrid - ", "", regex=True)
        .value_counts()
        .head(top_n)
        .reset_index()
    )
    loc.columns = ["location", "count"]
    return loc


def get_work_type_distribution(df: pd.DataFrame) -> pd.DataFrame:
    """Return distribution of work types (Full-time, Contract, etc.)."""
    if "work_type" not in df.columns:
        return pd.DataFrame()
    dist = df["work_type"].value_counts().reset_index()
    dist.columns = ["work_type", "count"]
    dist["pct"] = (dist["count"] / dist["count"].sum() * 100).round(1)
    return dist
