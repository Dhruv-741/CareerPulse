"""
CareerPulse — pytest test suite.

Tests cover:
- Data cleaning and preprocessing logic
- Profile matching scoring formula
- Roadmap generation
- Model prediction (smoke test)
- Edge cases and error handling
"""

import sys
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))


# ─── Preprocessing tests ──────────────────────────────────────────────────────

class TestPreprocessing:
    def test_clean_text_removes_html(self):
        from src.preprocessing import clean_text
        result = clean_text("<b>Hello World</b>")
        assert "<b>" not in result
        assert "hello world" in result

    def test_clean_text_handles_none(self):
        from src.preprocessing import clean_text
        result = clean_text(None)
        assert result == ""

    def test_normalize_experience_level_known(self):
        from src.preprocessing import normalize_experience_level
        assert normalize_experience_level("Entry level") == "Entry level"
        assert normalize_experience_level("Entry-Level") == "Entry level"
        assert normalize_experience_level("Junior") == "Entry level"
        assert normalize_experience_level("Mid-Senior level") == "Mid-Senior level"

    def test_normalize_experience_level_unknown(self):
        from src.preprocessing import normalize_experience_level
        result = normalize_experience_level("Unkn0wn Level")
        assert isinstance(result, str)

    def test_clean_dataframe_removes_duplicates(self):
        from src.preprocessing import clean_dataframe
        df = pd.DataFrame({
            "job_id": [1, 2, 2, 3],
            "title": ["Data Scientist"] * 4,
            "company_id": [1, 2, 2, 3],
            "description": ["desc " + str(i) for i in [1, 2, 2, 3]],
            "formatted_experience_level": ["Entry level"] * 4,
            "listed_time": ["2023-01-01"] * 4,
            "work_type": ["Full-time"] * 4,
            "location": ["Remote"] * 4,
            "skills_required": ["Python|SQL"] * 4,
        })
        cleaned = clean_dataframe(df)
        assert cleaned["job_id"].is_unique

    def test_clean_dataframe_parses_dates(self):
        from src.preprocessing import clean_dataframe
        df = pd.DataFrame({
            "job_id": range(5),
            "title": ["Eng"] * 5,
            "company_id": [1] * 5,
            "description": ["desc"] * 5,
            "formatted_experience_level": ["Entry level"] * 5,
            "listed_time": ["2023-06-15"] * 5,
            "work_type": ["Full-time"] * 5,
            "location": ["Remote"] * 5,
            "skills_required": ["Python"] * 5,
        })
        cleaned = clean_dataframe(df)
        assert "post_year" in cleaned.columns
        assert cleaned["post_year"].iloc[0] == 2023

    def test_split_proportions(self):
        from src.preprocessing import split_data, clean_dataframe
        df = pd.DataFrame({
            "job_id": range(1000),
            "title": [f"Data Scientist {i%5}" for i in range(1000)],
            "company_id": range(1000),
            "description": [f"Unique job posting description number {i} with skills " * 5 for i in range(1000)],
            "formatted_experience_level": ["Entry level"] * 500 + ["Senior"] * 500,
            "listed_time": pd.date_range("2023-01-01", periods=1000, freq="h").strftime("%Y-%m-%d %H:%M:%S").tolist(),
            "work_type": ["Full-time"] * 1000,
            "location": ["Remote"] * 1000,
            "skills_required": ["Python|SQL"] * 1000,
        })
        df_clean = clean_dataframe(df)
        train, val, test = split_data(df_clean, test_size=0.15, val_size=0.15)
        total = len(train) + len(val) + len(test)
        assert total == len(df_clean)
        assert abs(len(test) / total - 0.15) < 0.02
        assert abs(len(val) / total - 0.15) < 0.02


# ─── Profile matcher tests ────────────────────────────────────────────────────

class TestProfileMatcher:
    def test_perfect_match(self):
        from src.profile_matcher import compute_profile_match
        result = compute_profile_match(
            user_skills=["python", "sql", "pandas"],
            user_experience_level="Entry level",
            job_required_skills=["python", "sql", "pandas"],
            job_experience_level="Entry level",
        )
        assert result["match_score"] > 80
        assert len(result["missing_skills"]) == 0

    def test_no_skill_match(self):
        from src.profile_matcher import compute_profile_match
        result = compute_profile_match(
            user_skills=["html", "css"],
            user_experience_level="Entry level",
            job_required_skills=["python", "tensorflow", "spark"],
            job_experience_level="Mid-Senior level",
        )
        assert result["match_score"] < 40
        assert len(result["missing_skills"]) == 3

    def test_match_score_in_range(self):
        from src.profile_matcher import compute_profile_match
        result = compute_profile_match(
            user_skills=["python"],
            user_experience_level="Entry level",
            job_required_skills=["python", "sql", "r"],
            job_experience_level="Mid-Senior level",
        )
        assert 0 <= result["match_score"] <= 100

    def test_experience_level_score(self):
        from src.profile_matcher import experience_level_score
        assert experience_level_score("Entry level", "Entry level") == 1.0
        assert experience_level_score("Entry level", "Senior") < 0.5
        assert experience_level_score(None, "Senior") == 0.5

    def test_parse_skill_list_comma(self):
        from src.profile_matcher import parse_skill_list
        skills = parse_skill_list("Python, SQL, Git")
        assert "python" in skills
        assert "sql" in skills
        assert len(skills) == 3

    def test_parse_skill_list_pipe(self):
        from src.profile_matcher import parse_skill_list
        skills = parse_skill_list("Python|SQL|Git")
        assert len(skills) == 3


# ─── Roadmap tests ────────────────────────────────────────────────────────────

class TestRoadmap:
    def test_roadmap_returns_stages(self):
        from src.roadmap import get_roadmap
        roadmap = get_roadmap("Data Science", ["TensorFlow", "PyTorch"], "Entry level")
        assert "stages" in roadmap
        assert len(roadmap["stages"]) >= 1

    def test_roadmap_highlights_missing_skills(self):
        from src.roadmap import get_roadmap
        roadmap = get_roadmap("Data Science", ["TensorFlow"], "Entry level")
        all_missing = []
        for stage in roadmap["stages"]:
            all_missing.extend(stage.get("missing_here", []))
        assert "TensorFlow" in all_missing

    def test_roadmap_unknown_domain_uses_default(self):
        from src.roadmap import get_roadmap
        roadmap = get_roadmap("Quantum Physics", [], "Entry level")
        assert "stages" in roadmap
        assert len(roadmap["stages"]) >= 1

    def test_roadmap_next_steps_non_empty(self):
        from src.roadmap import get_roadmap
        roadmap = get_roadmap("Machine Learning", ["Docker", "Kubernetes"], "Entry level")
        assert len(roadmap["next_steps"]) >= 1

    def test_roadmap_resources_have_urls(self):
        from src.roadmap import get_roadmap
        roadmap = get_roadmap("Software Development", ["Docker"], "Entry level")
        for stage in roadmap["stages"]:
            for res in stage.get("resources", []):
                assert "url" in res
                assert res["url"].startswith("http")


# ─── Market analytics tests ───────────────────────────────────────────────────

class TestMarketAnalytics:
    @pytest.fixture
    def sample_df(self):
        return pd.DataFrame({
            "domain": ["Data Science", "ML", "Data Science"] * 10,
            "title": ["Data Scientist", "ML Engineer", "Data Scientist"] * 10,
            "company_id": [1, 2, 3] * 10,
            "post_year": [2023, 2024, 2023] * 10,
            "post_month": [1, 6, 12] * 10,
            "formatted_experience_level": ["Entry level", "Senior", "Mid-Senior level"] * 10,
            "location": ["Remote", "New York, NY", "San Francisco, CA"] * 10,
            "work_type": ["Full-time", "Contract", "Full-time"] * 10,
            "skills_required": ["Python|SQL", "Python|TensorFlow", "SQL|R"] * 10,
            "salary_midpoint": [80000, 150000, np.nan] * 10,
        })

    def test_postings_by_year(self, sample_df):
        from src.market_analytics import get_postings_by_year
        result = get_postings_by_year(sample_df)
        assert len(result) >= 1
        assert "posting_count" in result.columns

    def test_top_skills_returns_dataframe(self, sample_df):
        from src.market_analytics import get_top_skills
        result = get_top_skills(sample_df, domain="Data Science")
        assert isinstance(result, pd.DataFrame)
        assert "skill" in result.columns

    def test_salary_stats_with_data(self, sample_df):
        from src.market_analytics import get_salary_stats
        stats = get_salary_stats(sample_df)
        assert stats["available"] is True or stats.get("reason") is not None

    def test_experience_distribution(self, sample_df):
        from src.market_analytics import get_experience_distribution
        result = get_experience_distribution(sample_df, domain="Data Science")
        assert isinstance(result, pd.DataFrame)


# ─── Edge cases ───────────────────────────────────────────────────────────────

class TestEdgeCases:
    def test_empty_skill_list_profile_match(self):
        from src.profile_matcher import compute_profile_match
        result = compute_profile_match(
            user_skills=[],
            user_experience_level="Entry level",
            job_required_skills=["python", "sql"],
            job_experience_level="Entry level",
        )
        assert 0 <= result["match_score"] <= 100

    def test_empty_required_skills(self):
        from src.profile_matcher import compute_profile_match
        result = compute_profile_match(
            user_skills=["python"],
            user_experience_level="Entry level",
            job_required_skills=[],
            job_experience_level="Entry level",
        )
        assert result["match_score"] >= 0

    def test_market_analytics_empty_domain(self):
        from src.market_analytics import get_top_skills
        df = pd.DataFrame({
            "domain": ["Data Science"],
            "title": ["DS"],
            "skills_required": ["Python"],
        })
        result = get_top_skills(df, domain="Nonexistent")
        assert len(result) == 0
