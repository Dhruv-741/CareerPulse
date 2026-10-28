"""
CareerPulse — Candidate profile matcher.

Computes an explainable "Profile Match Score" (also called "Skill and
Experience Fit Score") by comparing a user's skills and experience
against the requirements extracted from dataset job postings.

IMPORTANT DISCLAIMERS (also shown in the UI):
- This score is NOT a probability of being hired.
- It reflects structural alignment between a user's profile and job posting
  requirements in the dataset — not hiring outcome.
- Hiring probability cannot be reliably learned from job posting data alone
  because applicant-level outcome data is unavailable.
- The scoring formula is fully transparent and configurable.

Formula (documented below):
  Match Score = 0.55 * skill_overlap_score
              + 0.30 * experience_level_score
              + 0.15 * additional_skills_bonus
  (All components normalized to [0, 1])
"""

import logging
from typing import List, Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Weights for the profile match score components
WEIGHTS = {
    "skill_overlap": 0.55,
    "experience_level": 0.30,
    "additional_skills": 0.15,
}

# Experience level ordering for compatibility scoring
EXP_ORDER = [
    "Entry level",
    "Associate",
    "Mid-Senior level",
    "Senior",
    "Director",
    "Executive",
]


def normalize_skill(skill: str) -> str:
    """Lowercase and strip a skill string."""
    return skill.strip().lower()


def parse_skill_list(skills_input) -> List[str]:
    """
    Parse a skill list from various input formats:
    - Comma-separated string: "Python, SQL, Git"
    - Pipe-separated string:  "Python|SQL|Git"
    - Python list
    """
    if isinstance(skills_input, list):
        return [normalize_skill(s) for s in skills_input if s]
    if isinstance(skills_input, str):
        sep = "|" if "|" in skills_input else ","
        return [normalize_skill(s) for s in skills_input.split(sep) if s.strip()]
    return []


def experience_level_score(
    user_level: str,
    required_level: str,
) -> float:
    """
    Score experience level compatibility [0.0 – 1.0].

    - Exact match: 1.0
    - One level off: 0.7
    - Two levels off: 0.4
    - More: 0.1
    - Unknown/missing: 0.5 (neutral)
    """
    if not user_level or not required_level:
        return 0.5

    user_idx = EXP_ORDER.index(user_level) if user_level in EXP_ORDER else -1
    req_idx = EXP_ORDER.index(required_level) if required_level in EXP_ORDER else -1

    if user_idx == -1 or req_idx == -1:
        return 0.5

    diff = abs(user_idx - req_idx)
    if diff == 0:
        return 1.0
    elif diff == 1:
        return 0.7
    elif diff == 2:
        return 0.4
    else:
        return 0.1


def compute_skill_overlap(
    user_skills: List[str],
    required_skills: List[str],
) -> Tuple[List[str], List[str], float]:
    """
    Compute skill overlap between user profile and job requirements.

    Returns
    -------
    matching_skills : skills the user has that are required
    missing_skills  : required skills the user does not have
    overlap_score   : |matching| / |required| (Jaccard-like)
    """
    user_set = set(user_skills)
    req_set = set(required_skills)

    matching = list(user_set & req_set)
    missing = list(req_set - user_set)

    if len(req_set) == 0:
        return matching, missing, 1.0

    overlap_score = len(matching) / len(req_set)
    return matching, missing, float(overlap_score)


def compute_profile_match(
    user_skills: List[str],
    user_experience_level: str,
    job_required_skills: List[str],
    job_experience_level: str,
) -> dict:
    """
    Compute the full Profile Match Score for a user against a single job.

    Returns a dict with:
    - match_score       : float [0, 100]
    - matching_skills   : list
    - missing_skills    : list
    - exp_score         : float [0, 1]
    - skill_score       : float [0, 1]
    - bonus_score       : float [0, 1]
    - explanation       : str
    """
    user_normalized = [normalize_skill(s) for s in user_skills]
    req_normalized = [normalize_skill(s) for s in job_required_skills]

    matching, missing, skill_score = compute_skill_overlap(user_normalized, req_normalized)
    exp_score = experience_level_score(user_experience_level, job_experience_level)

    # Additional skills bonus: user has skills BEYOND the requirements
    bonus_skills = list(set(user_normalized) - set(req_normalized))
    bonus_score = min(1.0, len(bonus_skills) / max(1, len(req_normalized)) * 2)

    raw_score = (
        WEIGHTS["skill_overlap"] * skill_score
        + WEIGHTS["experience_level"] * exp_score
        + WEIGHTS["additional_skills"] * bonus_score
    )
    match_score = round(raw_score * 100, 1)

    explanation = (
        f"Skill overlap: {len(matching)}/{len(req_normalized)} required skills matched "
        f"(score: {skill_score:.2f}). "
        f"Experience compatibility with '{job_experience_level}': {exp_score:.2f}. "
        f"You have {len(bonus_skills)} additional skill(s) not specifically required. "
        f"Formula: 0.55×{skill_score:.2f} + 0.30×{exp_score:.2f} + 0.15×{bonus_score:.2f} = {raw_score:.2f}"
    )

    return {
        "match_score": match_score,
        "matching_skills": [s.title() for s in matching],
        "missing_skills": [s.title() for s in missing],
        "additional_skills": [s.title() for s in bonus_skills],
        "skill_score": round(skill_score, 3),
        "exp_score": round(exp_score, 3),
        "bonus_score": round(bonus_score, 3),
        "explanation": explanation,
    }


def find_matching_jobs(
    df: pd.DataFrame,
    user_skills: List[str],
    user_experience_level: str,
    domain: str,
    role: str = "",
    top_n: int = 10,
    companies_df: pd.DataFrame = None,
) -> pd.DataFrame:
    """
    Find jobs in the dataset that best match the user's profile.

    Returns top_n jobs ranked by Profile Match Score.
    """
    filtered = df.copy()

    if domain and domain != "All":
        filtered = filtered[filtered["domain"] == domain]

    if role and role.strip():
        filtered = filtered[
            filtered["title"].str.contains(role, case=False, na=False)
        ]

    if len(filtered) == 0:
        return pd.DataFrame()

    # Compute match score for a sample (performance: max 500 jobs)
    sample = filtered.head(500).copy()

    scores = []
    for _, row in sample.iterrows():
        job_skills = parse_skill_list(row.get("skills_required", ""))
        job_exp = str(row.get("formatted_experience_level", ""))
        result = compute_profile_match(user_skills, user_experience_level, job_skills, job_exp)
        scores.append(result["match_score"])

    sample["match_score"] = scores
    sample = sample.sort_values("match_score", ascending=False).head(top_n)

    # Merge company name
    if companies_df is not None and "company_id" in sample.columns:
        sample = sample.merge(
            companies_df[["company_id", "name"]].rename(columns={"name": "company_name"}),
            on="company_id",
            how="left",
        )

    cols = [c for c in ["title", "company_name", "location", "formatted_experience_level",
                         "work_type", "match_score", "skills_required", "post_year"] if c in sample.columns]
    return sample[cols].reset_index(drop=True)
