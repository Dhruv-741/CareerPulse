"""
CareerPulse — Streamlit Application Entry Point.

Provides a polished, multi-section interface for:
  1. Home and Project Overview
  2. Job Market Explorer
  3. Company and Role Analytics
  4. Candidate Profile Matcher
  5. Skill Gap Analysis and Learning Roadmap
  6. Model Performance and Explainability
  7. Data Sources, Methodology, and Limitations
"""

import sys
import os
import json
import logging
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

# ── Conditional imports for optional packages ─────────────────────────────────
try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False

try:
    import plotly.express as px
    import plotly.graph_objects as go
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

sys.path.insert(0, str(Path(__file__).parent))

logging.basicConfig(level=logging.WARNING)

# ─── Constants ────────────────────────────────────────────────────────────────
APP_TITLE = "CareerPulse"
APP_SUBTITLE = "AI-Powered Job Market Intelligence & Career Readiness Analyzer"
VERSION = "1.0.0"
DATASET_NOTE = (
    "📊 **Dataset**: Synthetic dataset modelling LinkedIn Job Postings (2023–2024) "
    "by Arsh Koneru (Kaggle). ~15,000 postings. Coverage: Jan 2023 – Dec 2024."
)
POSTING_DISCLAIMER = (
    "⚠️ **Disclaimer**: Job posting counts are a proxy for observable recruitment "
    "activity in the dataset — they are NOT confirmed employee hires. This dataset "
    "covers a historical snapshot (2023–2024) and does not reflect current live openings."
)

DOMAINS = [
    "All", "Data Science", "Machine Learning", "Software Development",
    "Data Engineering", "Cybersecurity", "Cloud Computing", "Web Development"
]

EXP_LEVELS = [
    "Entry level", "Associate", "Mid-Senior level", "Senior", "Director", "Executive"
]

# ─── Data loading with caching ────────────────────────────────────────────────
@st.cache_data(show_spinner="Loading dataset…")
def load_data():
    """Load and cache the processed dataset. Run pipeline first if needed."""
    from src.data_loader import load_processed_data, load_raw_data, load_dataset_metadata
    df = load_processed_data()
    if df is None:
        # Auto-run data generation + cleaning
        _bootstrap_data()
        df = load_processed_data()
    companies = pd.read_csv("data/raw/companies.csv") if Path("data/raw/companies.csv").exists() else pd.DataFrame()
    meta = load_dataset_metadata()
    return df, companies, meta


def _bootstrap_data():
    """Generate synthetic data and run cleaning pipeline if not done yet."""
    import subprocess, sys
    result = subprocess.run(
        [sys.executable, "scripts/generate_synthetic_data.py"],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        st.error(f"Data generation failed: {result.stderr[:500]}")
        return

    from src.data_loader import load_raw_data
    from src.preprocessing import clean_dataframe
    jobs, companies, skills = load_raw_data()
    df_clean = clean_dataframe(jobs)
    Path("data/processed").mkdir(parents=True, exist_ok=True)
    df_clean.to_csv("data/processed/jobs_clean.csv", index=False)


@st.cache_data(show_spinner="Loading model results…")
def load_model_results():
    """Load pre-computed model comparison results."""
    path = Path("data/processed/model_results.csv")
    if path.exists():
        return pd.read_csv(path, index_col=0)
    return None


@st.cache_data(show_spinner="Loading test results…")
def load_test_results():
    path = Path("data/processed/best_model_test_results.json")
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return None


# ─── Helper chart functions ───────────────────────────────────────────────────
def _bar_chart_plotly(df, x, y, title, color=None, orientation="v"):
    if PLOTLY_AVAILABLE:
        if orientation == "h":
            fig = px.bar(df, y=x, x=y, title=title, color=color,
                         orientation="h", color_discrete_sequence=px.colors.qualitative.Set2)
        else:
            fig = px.bar(df, x=x, y=y, title=title, color=color,
                         color_discrete_sequence=px.colors.qualitative.Set2)
        fig.update_layout(margin=dict(l=10, r=10, t=40, b=10))
        st.plotly_chart(fig, use_container_width=True)
    else:
        # Matplotlib fallback
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.bar(df[x], df[y], color="#2196F3", alpha=0.85)
        ax.set_title(title)
        ax.set_xlabel(x)
        ax.set_ylabel(y)
        plt.xticks(rotation=30, ha="right")
        plt.tight_layout()
        st.pyplot(fig)
        plt.close(fig)


def _line_chart_plotly(df, x, y, color, title):
    if PLOTLY_AVAILABLE:
        fig = px.line(df, x=x, y=y, color=color, title=title,
                      color_discrete_sequence=px.colors.qualitative.Set2,
                      markers=True)
        fig.update_layout(margin=dict(l=10, r=10, t=40, b=10))
        st.plotly_chart(fig, use_container_width=True)
    else:
        fig, ax = plt.subplots(figsize=(8, 4))
        for key, grp in df.groupby(color):
            ax.plot(grp[x], grp[y], marker="o", label=key)
        ax.set_title(title)
        ax.legend(fontsize=7, loc="best")
        plt.tight_layout()
        st.pyplot(fig)
        plt.close(fig)


def _pie_chart(labels, values, title):
    if PLOTLY_AVAILABLE:
        fig = px.pie(names=labels, values=values, title=title,
                     color_discrete_sequence=px.colors.qualitative.Set2)
        fig.update_layout(margin=dict(l=10, r=10, t=40, b=10))
        st.plotly_chart(fig, use_container_width=True)
    else:
        fig, ax = plt.subplots(figsize=(5, 4))
        ax.pie(values, labels=labels, autopct="%1.0f%%")
        ax.set_title(title)
        plt.tight_layout()
        st.pyplot(fig)
        plt.close(fig)


# ─── Page: Home ──────────────────────────────────────────────────────────────
def page_home(df, meta):
    st.markdown(f"# 🎯 {APP_TITLE}")
    st.markdown(f"### {APP_SUBTITLE}")
    st.markdown("---")

    col1, col2, col3, col4 = st.columns(4)
    n_jobs = len(df) if df is not None else 0
    n_companies = df["company_id"].nunique() if df is not None and "company_id" in df.columns else 0
    n_domains = df["domain"].nunique() if df is not None and "domain" in df.columns else 0
    years = sorted(df["post_year"].dropna().unique().astype(int).tolist()) if df is not None and "post_year" in df.columns else []

    col1.metric("📋 Job Postings", f"{n_jobs:,}")
    col2.metric("🏢 Companies", f"{n_companies:,}")
    col3.metric("🗂 Domains", f"{n_domains:,}")
    col4.metric("📅 Coverage", f"{years[0]}–{years[-1]}" if years else "N/A")

    st.info(DATASET_NOTE)
    st.warning(POSTING_DISCLAIMER)

    st.markdown("---")
    st.markdown("## What CareerPulse Does")
    cols = st.columns(3)
    with cols[0]:
        st.markdown("### 📊 Job Market Intelligence")
        st.markdown("- Posting trends by year, domain, company\n- Top in-demand skills\n- Salary distributions\n- Location and work-type breakdowns")
    with cols[1]:
        st.markdown("### 🎯 Profile Matching")
        st.markdown("- Enter your skills and experience\n- Get an explainable fit score\n- See matching & missing skills\n- Find relevant postings in data")
    with cols[2]:
        st.markdown("### 🗺 Learning Roadmap")
        st.markdown("- Personalized skill-gap analysis\n- Stage-based learning path\n- Verified learning resources\n- Project suggestions")

    st.markdown("---")
    st.markdown("## How to Use")
    st.markdown("""
1. **Job Market Explorer** — Explore posting trends and skill demand by domain and year.
2. **Company & Role Analytics** — See which companies post most for your target role.
3. **Profile Matcher** — Enter your skills → get a transparency-first fit score.
4. **Skill Gap & Roadmap** — Get a personalized learning plan for missing skills.
5. **Model Performance** — Inspect the ML model that predicts experience levels.
6. **Data Sources** — Full dataset provenance and methodology.
    """)


# ─── Page: Job Market Explorer ────────────────────────────────────────────────
def page_job_market(df, companies):
    st.markdown("# 📊 Job Market Explorer")
    st.info(POSTING_DISCLAIMER)

    from src.market_analytics import (
        get_postings_by_year, get_postings_by_year_domain,
        get_top_skills, get_experience_distribution,
        get_salary_stats, get_work_type_distribution,
        get_location_distribution,
    )

    col1, col2 = st.columns(2)
    with col1:
        domain_filter = st.selectbox("Domain", DOMAINS, key="market_domain")
    with col2:
        year_options = sorted(df["post_year"].dropna().unique().astype(int).tolist()) if "post_year" in df.columns else []
        year_filter = st.multiselect("Year(s)", year_options, default=year_options, key="market_year")

    filtered = df.copy()
    if domain_filter != "All":
        filtered = filtered[filtered["domain"] == domain_filter]
    if year_filter:
        filtered = filtered[filtered["post_year"].isin(year_filter)]

    if len(filtered) == 0:
        st.warning("No data for current filters.")
        return

    st.markdown(f"**Showing {len(filtered):,} postings**")
    st.markdown("---")

    # Posting trend
    st.subheader("📈 Posting Trend by Year")
    trend = get_postings_by_year(filtered)
    if len(trend) > 0:
        _bar_chart_plotly(trend, x="post_year", y="posting_count",
                         title="Job Postings by Year (Not actual hires)")

    # Domain breakdown
    st.subheader("🗂 Postings by Domain and Year")
    domain_year = get_postings_by_year_domain(filtered)
    if len(domain_year) > 0:
        _line_chart_plotly(domain_year, x="post_year", y="posting_count",
                          color="domain", title="Posting Trends by Domain")

    st.markdown("---")
    col1, col2 = st.columns(2)

    # Top skills
    with col1:
        st.subheader("🔧 Top Requested Skills")
        skills_data = get_top_skills(filtered, top_n=15)
        if len(skills_data) > 0:
            _bar_chart_plotly(skills_data, x="skill", y="count",
                             title=f"Top Skills — {domain_filter}", orientation="v")

    # Experience distribution
    with col2:
        st.subheader("👔 Experience Level Distribution")
        exp_dist = get_experience_distribution(filtered, domain=domain_filter)
        if len(exp_dist) > 0:
            _pie_chart(
                labels=exp_dist["experience_level"].tolist(),
                values=exp_dist["count"].tolist(),
                title="Experience Level Distribution",
            )

    st.markdown("---")
    col1, col2 = st.columns(2)

    # Salary
    with col1:
        st.subheader("💰 Salary Distribution")
        sal_stats = get_salary_stats(filtered, domain=domain_filter)
        if sal_stats.get("available"):
            st.markdown(fr"""
| Metric | Value |
|--------|-------|
| Median Salary | \${sal_stats['median_usd']:,} |
| Mean Salary | \${sal_stats['mean_usd']:,} |
| 25th Percentile | \${sal_stats['p25_usd']:,} |
| 75th Percentile | \${sal_stats['p75_usd']:,} |
| Range | \${sal_stats['min_usd']:,} – \${sal_stats['max_usd']:,} |
| Postings with Salary | {sal_stats['n_with_salary']:,} ({sal_stats['pct_with_salary']}%) |
            """)
            st.caption("*All figures in USD (Annual). Only postings with salary data included.*")
        else:
            st.info(f"Salary data: {sal_stats.get('reason', 'Not available')}")

    # Work type
    with col2:
        st.subheader("⏰ Work Type Distribution")
        wt_dist = get_work_type_distribution(filtered)
        if len(wt_dist) > 0:
            _pie_chart(
                labels=wt_dist["work_type"].tolist(),
                values=wt_dist["count"].tolist(),
                title="Work Type",
            )

    # Location
    st.subheader("📍 Top Locations")
    loc_data = get_location_distribution(filtered, top_n=12)
    if len(loc_data) > 0:
        _bar_chart_plotly(loc_data, x="location", y="count",
                         title="Postings by Location", orientation="v")


# ─── Page: Company & Role Analytics ──────────────────────────────────────────
def page_company_analytics(df, companies):
    st.markdown("# 🏢 Company & Role Analytics")
    st.info(POSTING_DISCLAIMER)

    from src.market_analytics import get_top_companies, get_role_trends

    col1, col2 = st.columns(2)
    with col1:
        domain_filter = st.selectbox("Domain", DOMAINS, key="comp_domain")
    with col2:
        role_filter = st.text_input("Search Role (optional)", placeholder="e.g. Data Scientist", key="comp_role")

    st.markdown("---")
    st.subheader("🏆 Top Companies by Posting Volume")
    st.caption("Posting count = number of job ads in the dataset. Not a measure of headcount or actual hires.")

    top_companies = get_top_companies(df, companies, domain=domain_filter, role=role_filter, top_n=15)
    if len(top_companies) > 0:
        _bar_chart_plotly(
            top_companies,
            x="name" if "name" in top_companies.columns else "company_id",
            y="posting_count",
            title=f"Top Companies — {domain_filter} | {role_filter or 'All Roles'}",
            orientation="v",
        )
        st.dataframe(top_companies[["name", "posting_count", "industry", "headquarters"]].head(10)
                     if all(c in top_companies.columns for c in ["name", "industry", "headquarters"])
                     else top_companies.head(10),
                     use_container_width=True)
    else:
        st.info("No company data for current filters.")

    st.markdown("---")
    st.subheader("📈 Role Trends Over Time")
    role_trends = get_role_trends(df, domain=domain_filter, top_n_roles=6)
    if len(role_trends) > 0:
        _line_chart_plotly(role_trends, x="post_year", y="posting_count",
                          color="title", title=f"Top Role Trends — {domain_filter}")
    else:
        st.info("Insufficient temporal data for role trends.")


# ─── Page: Profile Matcher ────────────────────────────────────────────────────
def page_profile_matcher(df, companies):
    st.markdown("# 🎯 Candidate Profile Matcher")

    st.warning("""
**Important**: The **Profile Match Score** measures structural alignment between your stated
skills/experience and job posting requirements in the dataset.
It is **NOT** a probability of getting hired — hiring outcomes depend on many factors
(interview performance, cultural fit, timing, competition) not captured in job posting data.
See the scoring formula below for full transparency.
    """)

    st.markdown("---")
    st.subheader("📝 Your Profile")

    col1, col2 = st.columns(2)
    with col1:
        target_domain = st.selectbox("Target Domain", DOMAINS[1:], key="pm_domain")
        target_role = st.text_input("Target Role", placeholder="e.g. Data Scientist", key="pm_role")
        user_level = st.selectbox("Your Experience Level", EXP_LEVELS, key="pm_level")
    with col2:
        user_skills_input = st.text_area(
            "Your Skills (comma-separated)",
            placeholder="Python, SQL, Pandas, Machine Learning, Git",
            height=100,
            key="pm_skills"
        )
        preferred_companies = st.text_input("Preferred Companies (optional, comma-separated)", key="pm_companies")

    st.markdown("---")
    if st.button("🔍 Analyze My Profile", type="primary", key="pm_analyze"):
        if not user_skills_input.strip():
            st.error("Please enter at least one skill.")
            return

        from src.profile_matcher import parse_skill_list, find_matching_jobs, compute_profile_match
        from src.market_analytics import get_top_skills

        user_skills = parse_skill_list(user_skills_input)

        with st.spinner("Analyzing your profile against job postings…"):
            # Find matching jobs
            matching_jobs = find_matching_jobs(
                df, user_skills, user_level, target_domain, target_role,
                top_n=10, companies_df=companies if len(companies) > 0 else None
            )

            # Aggregate skill requirements for target domain/role
            filtered = df.copy()
            if target_domain != "All":
                filtered = filtered[filtered["domain"] == target_domain]
            if target_role.strip():
                filtered = filtered[filtered["title"].str.contains(target_role, case=False, na=False)]

            top_skills = get_top_skills(filtered, top_n=20)
            if len(top_skills) > 0:
                required_skills = top_skills["skill"].str.lower().tolist()
            else:
                required_skills = []

        # Compute aggregate match against top role skills
        agg_result = compute_profile_match(
            user_skills=user_skills,
            user_experience_level=user_level,
            job_required_skills=required_skills[:15],
            job_experience_level="Mid-Senior level",  # neutral reference
        )

        # Score display
        score = agg_result["match_score"]
        score_color = "🟢" if score >= 70 else "🟡" if score >= 45 else "🔴"
        st.markdown(f"## {score_color} Profile Match Score: **{score:.1f} / 100**")

        with st.expander("📐 How this score is calculated"):
            st.markdown(f"""
**Formula** (weights configurable):
```
Match Score = 0.55 × Skill Overlap Score
            + 0.30 × Experience Compatibility Score
            + 0.15 × Additional Skills Bonus
```
**Your score breakdown:**
- Skill Overlap Score: **{agg_result['skill_score']:.2f}** — {len(agg_result['matching_skills'])}/{len(required_skills[:15])} required skills matched
- Experience Compatibility: **{agg_result['exp_score']:.2f}** — your level vs. typical job requirements
- Additional Skills Bonus: **{agg_result['bonus_score']:.2f}** — you have {len(agg_result['additional_skills'])} extra skills beyond requirements

*This score does not predict hiring probability. It is a transparent structural alignment indicator.*
            """)

        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("### ✅ Matching Skills")
            if agg_result["matching_skills"]:
                for s in agg_result["matching_skills"]:
                    st.markdown(f"- {s}")
            else:
                st.info("No direct skill matches found.")
        with col2:
            st.markdown("### ❌ Missing Skills")
            if agg_result["missing_skills"]:
                for s in agg_result["missing_skills"][:10]:
                    st.markdown(f"- {s}")
            else:
                st.success("No major skill gaps identified!")
        with col3:
            st.markdown("### ➕ Your Extra Skills")
            if agg_result["additional_skills"]:
                for s in agg_result["additional_skills"][:8]:
                    st.markdown(f"- {s}")
            else:
                st.info("No additional skills beyond requirements.")

        st.markdown("---")
        st.subheader("💼 Best Matching Jobs in Dataset")
        if len(matching_jobs) > 0:
            display_cols = [c for c in ["title", "company_name", "location",
                                        "formatted_experience_level", "match_score", "post_year"]
                           if c in matching_jobs.columns]
            st.dataframe(
                matching_jobs[display_cols].rename(columns={
                    "title": "Role", "company_name": "Company",
                    "formatted_experience_level": "Exp. Level",
                    "match_score": "Match Score", "post_year": "Year",
                }),
                use_container_width=True
            )
            st.caption("Matching jobs are from the 2023-2024 dataset snapshot, not live listings.")
        else:
            st.info("No matching jobs found for the given filters. Try a broader domain or role.")


# ─── Page: Skill Gap & Roadmap ────────────────────────────────────────────────
def page_roadmap(df):
    st.markdown("# 🗺 Skill Gap Analysis & Learning Roadmap")
    st.markdown("Generate a personalized learning roadmap based on your target role and missing skills.")

    col1, col2 = st.columns(2)
    with col1:
        target_domain = st.selectbox("Target Domain", DOMAINS[1:], key="rm_domain")
        user_level = st.selectbox("Your Current Level", EXP_LEVELS, key="rm_level")
    with col2:
        user_skills_input = st.text_area(
            "Your Current Skills (comma-separated)",
            placeholder="Python, SQL, Git",
            height=100, key="rm_skills"
        )

    if st.button("🗺 Generate Roadmap", type="primary", key="rm_generate"):
        from src.profile_matcher import parse_skill_list
        from src.market_analytics import get_top_skills
        from src.roadmap import get_roadmap

        user_skills = parse_skill_list(user_skills_input)

        filtered = df[df["domain"] == target_domain] if target_domain != "All" else df
        top_skills = get_top_skills(filtered, top_n=20)
        if len(top_skills) > 0:
            required_skills = top_skills["skill"].tolist()
            user_lower = [s.lower() for s in user_skills]
            missing_skills = [s for s in required_skills if s.lower() not in user_lower][:12]
        else:
            missing_skills = []

        roadmap = get_roadmap(target_domain, missing_skills, user_level)

        st.markdown(f"## 🗺 Roadmap for **{target_domain}**")
        st.markdown(f"📍 **Community Reference**: [roadmap.sh]({roadmap['roadmap_url']})")

        if missing_skills:
            st.markdown(f"**Priority Skills to Learn** (based on job postings in dataset):")
            st.markdown(" · ".join([f"`{s}`" for s in missing_skills[:8]]))
        else:
            st.success("You already have coverage of the top required skills!")

        st.markdown(f"**Recommended Focus Stage**: {roadmap['recommended_focus_stage']}")
        st.markdown("---")

        for stage in roadmap["stages"]:
            stage_emoji = {"Beginner": "🌱", "Intermediate": "🌿", "Advanced": "🌳"}.get(stage["name"], "📚")
            with st.expander(f"{stage_emoji} {stage['name']} Stage", expanded=(stage["name"] == roadmap["recommended_focus_stage"])):
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**Skills in this stage:**")
                    for skill in stage["skills"]:
                        if skill in stage["missing_here"]:
                            st.markdown(f"- ❌ **{skill}** ← *missing*")
                        else:
                            st.markdown(f"- ✅ {skill}")
                with col2:
                    st.markdown("**Projects to build:**")
                    for proj in stage["projects"]:
                        st.markdown(f"- {proj}")

                st.markdown("**Learning Resources:**")
                for res in stage["resources"]:
                    st.markdown(f"- [{res['name']}]({res['url']})")

        st.markdown("---")
        st.subheader("✅ Your Next Steps")
        for i, step in enumerate(roadmap["next_steps"], 1):
            st.markdown(f"{i}. {step}")


# ─── Page: Model Performance ──────────────────────────────────────────────────
def page_model_performance():
    st.markdown("# 🤖 Model Performance & Explainability")
    st.markdown("""
**Prediction Task**: Classify a job posting's experience level
(`Entry level`, `Associate`, `Mid-Senior level`, `Senior`, `Director`, `Executive`)
from its title, description text, and structured features.

**Why this task?** Experience level prediction enables the app to analyze posting requirements
at scale and calibrate the candidate profile scoring system.
    """)

    results_df = load_model_results()
    test_results = load_test_results()

    if results_df is None:
        st.warning("Model results not found. Run `python scripts/run_pipeline.py` first.")
        with st.expander("Run Pipeline Automatically"):
            if st.button("▶ Run Training Pipeline", key="run_pipeline"):
                import subprocess, sys
                with st.spinner("Training all models (this may take 2–5 minutes)…"):
                    result = subprocess.run(
                        [sys.executable, "scripts/run_pipeline.py"],
                        capture_output=True, text=True, cwd=str(Path.cwd())
                    )
                if result.returncode == 0:
                    st.success("Pipeline complete! Refresh the page.")
                else:
                    st.error(f"Pipeline error:\n```\n{result.stderr[-2000:]}\n```")
        return

    st.subheader("📊 Model Comparison — Validation Set")
    display_cols = [c for c in ["Accuracy", "Macro Precision", "Macro Recall",
                                 "Macro F1", "Weighted F1", "ROC-AUC (OVR)", "Train Time (s)"]
                   if c in results_df.columns]
    st.dataframe(
        results_df[display_cols].style.highlight_max(
            subset=["Macro F1"] if "Macro F1" in display_cols else [], color="#d4f1d4"
        ),
        use_container_width=True
    )

    st.caption("""
**Macro F1** is the primary selection metric because it treats all experience level classes equally,
regardless of class imbalance. Accuracy can be misleading when one class dominates.
    """)

    # Bar chart
    if PLOTLY_AVAILABLE and "Macro F1" in results_df.columns:
        plot_df = results_df[["Accuracy", "Macro F1", "Weighted F1"]].dropna(how="all").reset_index()
        plot_df = plot_df.melt(id_vars=["Model"], var_name="Metric", value_name="Score")
        fig = px.bar(plot_df, x="Model", y="Score", color="Metric", barmode="group",
                     title="Model Comparison — Validation Set",
                     color_discrete_sequence=px.colors.qualitative.Set2,
                     range_y=[0, 1.1])
        fig.update_layout(margin=dict(l=10, r=10, t=40, b=10))
        st.plotly_chart(fig, use_container_width=True)
    elif Path("figures/model_comparison.png").exists():
        st.image("figures/model_comparison.png", caption="Model Comparison Chart")

    st.markdown("---")
    if test_results:
        st.subheader(f"🏆 Best Model: {test_results['best_model']} — Final Test Set Results")
        st.info("⚠️ The test set was used only ONCE, after model selection on validation data, to prevent test-set contamination.")
        tcol1, tcol2, tcol3, tcol4 = st.columns(4)
        tcol1.metric("Accuracy", f"{test_results['test_accuracy']:.4f}")
        tcol2.metric("Macro F1", f"{test_results['test_macro_f1']:.4f}")
        tcol3.metric("Weighted F1", f"{test_results['test_weighted_f1']:.4f}")
        auc_val = test_results.get("test_roc_auc")
        tcol4.metric("ROC-AUC", f"{auc_val:.4f}" if auc_val else "N/A")

    if Path("figures/confusion_matrix_test.png").exists():
        st.subheader("Confusion Matrix — Test Set")
        st.image("figures/confusion_matrix_test.png", caption="Best Model Confusion Matrix (Test Set)")

    st.markdown("---")
    st.subheader("🔍 Predict Experience Level")
    st.markdown("Test the trained model on custom input:")
    pred_title = st.text_input("Job Title", value="Senior Data Scientist", key="pred_title")
    pred_desc = st.text_area("Job Description (optional)", key="pred_desc", height=80,
                             value="Looking for an experienced data scientist with 5+ years in ML and Python.")
    if st.button("Predict", key="pred_btn"):
        try:
            from src.train import load_model, predict_experience_level
            bundle = load_model(test_results["best_model"] if test_results else "")
            result = predict_experience_level(bundle, pred_title, pred_desc)
            st.success(f"**Predicted Experience Level**: {result['predicted_class']}")
            if result.get("class_probabilities"):
                prob_df = pd.DataFrame.from_dict(
                    result["class_probabilities"], orient="index", columns=["Probability"]
                ).sort_values("Probability", ascending=False)
                if PLOTLY_AVAILABLE:
                    fig = px.bar(prob_df.reset_index(), x="index", y="Probability",
                                 title="Class Probabilities", range_y=[0, 1])
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.dataframe(prob_df)
        except Exception as e:
            st.error(f"Prediction failed: {e}. Run the training pipeline first.")


# ─── Page: Data Sources & Methodology ────────────────────────────────────────
def page_data_sources(df, meta):
    st.markdown("# 📚 Data Sources, Methodology & Limitations")

    st.subheader("Dataset Provenance")
    st.markdown(f"""
| Field | Details |
|-------|---------|
| **Original Source** | LinkedIn Job Postings (2023-2024) |
| **Publisher** | Arsh Koneru |
| **Repository** | [kaggle.com/datasets/arshkon/linkedin-job-postings](https://www.kaggle.com/datasets/arshkon/linkedin-job-postings) |
| **License** | Open Database License (ODbL) |
| **Coverage** | January 2023 – December 2024 |
| **Note** | Synthetic dataset used (Kaggle auth unavailable); mirrors original schema |
| **Records** | {len(df):,} job postings |
| **Companies** | {df['company_id'].nunique() if 'company_id' in df.columns else 'N/A'} |
| **Unit of Observation** | Individual job posting |
    """)

    st.markdown("---")
    st.subheader("Data Cleaning Steps")
    st.markdown(r"""
| Step | Action | Rationale |
|------|---------|-----------|
| Duplicate removal | Removed duplicate `job_id` rows; near-duplicates (same title+company+description prefix) | Prevents inflated counts and data leakage |
| Date parsing | Parsed `listed_time` → `post_year`, `post_month` | Enables chronological splitting |
| Experience normalization | Standardized to 6 canonical levels | Consistent target labels |
| Missing experience level | Imputed to `Mid-Senior level` (mode); records with no label excluded from ML | Cannot train on unlabeled data |
| Missing location | Filled with "Unknown" | Prevents row loss; location not in ML features |
| Text cleaning | Stripped HTML, lowercased, removed special characters | Clean TF-IDF vocabulary |
| Salary cleaning | Removed values < \$10k or > \$5M annual | Remove implausible outliers |
    """)

    st.markdown("---")
    st.subheader("Train/Validation/Test Split")
    st.markdown("""
- **Strategy**: Chronological split (sorted by `post_year` and `post_month`)
- **Rationale**: Job market data has temporal structure. Chronological splitting avoids
  future data leaking into training, better simulating real deployment conditions.
- **Proportions**: 70% Train | 15% Validation | 15% Test
- **Random seed**: 42 (for all stochastic operations)
- **Deduplication**: Performed BEFORE splitting to prevent near-duplicate leakage across splits
- **Preprocessing**: TF-IDF vocabulary and IDF weights fitted on training data ONLY;
  then applied to val/test without refitting
    """)

    st.markdown("---")
    st.subheader("Machine Learning Task")
    st.markdown("""
**Target Variable**: `formatted_experience_level` — 6-class classification
(Entry level / Associate / Mid-Senior level / Senior / Director / Executive)

**Why this target?**
- Directly supported by dataset labels (no label engineering required)
- Useful for the application: enables automatic experience-level intelligence
- Connects to profile matching: the model captures what textual signals indicate seniority

**Features**:
- TF-IDF (max 5,000 features, bigrams, sublinear TF) on title + description (title weighted ×3)
- Structured: description length, skill count, remote indicator, year, month (sin/cos), work type

**What the model cannot do**:
- Predict whether a specific applicant will be hired
- Generalize to job domains not in the training data
- Detect salary negotiations, informal requirements, or ATS filtering
    """)

    st.markdown("---")
    st.subheader("⚠️ Limitations")
    st.markdown("""
1. **Synthetic data**: This deployment uses synthetically generated data. Real results may differ with the actual Kaggle dataset.
2. **No hiring outcomes**: Job postings ≠ actual hires. No applicant-level data is available.
3. **Historical snapshot**: Data covers 2023-2024 only. Market conditions change.
4. **Dataset size**: ~15,000 records (real dataset has 124,000+). Smaller sample affects model performance.
5. **Geographic bias**: Majority of postings are US-centric.
6. **Experience labels**: Some labels were imputed; ground truth label quality depends on original data.
7. **Skill taxonomy**: Skill matching is string-based; synonyms (e.g., "ML" vs "Machine Learning") may not match.
    """)


# ─── Main router ─────────────────────────────────────────────────────────────
def main():
    st.set_page_config(
        page_title=APP_TITLE,
        page_icon="🎯",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Custom CSS
    st.markdown("""
    <style>
    .main { padding-top: 1rem; }
    .stMetric { background: #f0f4ff; border-radius: 8px; padding: 8px; }
    h1 { color: #1a237e; }
    h2 { color: #283593; }
    h3 { color: #3949ab; }
    .stAlert { border-radius: 8px; }
    </style>
    """, unsafe_allow_html=True)

    with st.sidebar:
        st.markdown(f"## 🎯 {APP_TITLE}")
        st.markdown(f"*{APP_SUBTITLE}*")
        st.markdown("---")
        page = st.radio(
            "Navigate",
            [
                "🏠 Home",
                "📊 Job Market Explorer",
                "🏢 Company & Role Analytics",
                "🎯 Profile Matcher",
                "🗺 Skill Gap & Roadmap",
                "🤖 Model Performance",
                "📚 Data Sources & Methodology",
            ],
            label_visibility="collapsed"
        )
        st.markdown("---")
        st.markdown(f"**Version**: {VERSION}")
        st.markdown("**Dataset**: LinkedIn-style job postings (2023–2024)")
        st.markdown("[📄 View Report](reports/CareerPulse_Report.pdf)" if Path("reports/CareerPulse_Report.pdf").exists() else "")
        st.markdown("[💻 GitHub Repo](https://github.com)")

    # Load data (cached)
    try:
        df, companies, meta = load_data()
    except Exception as e:
        st.error(f"Data loading error: {e}")
        st.markdown("Run `python scripts/generate_synthetic_data.py` to generate data.")
        return

    if df is None or len(df) == 0:
        st.error("No data available. Please run the data pipeline first.")
        return

    # Route to selected page
    if "Home" in page:
        page_home(df, meta)
    elif "Job Market" in page:
        page_job_market(df, companies)
    elif "Company" in page:
        page_company_analytics(df, companies)
    elif "Profile Matcher" in page:
        page_profile_matcher(df, companies)
    elif "Roadmap" in page:
        page_roadmap(df)
    elif "Model Performance" in page:
        page_model_performance()
    elif "Data Sources" in page:
        page_data_sources(df, meta)


if __name__ == "__main__":
    if not STREAMLIT_AVAILABLE:
        print("Streamlit not installed. Install with: pip install streamlit")
        sys.exit(1)
    main()
