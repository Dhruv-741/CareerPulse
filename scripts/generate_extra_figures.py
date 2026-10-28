"""
CareerPulse — Generate supplementary figures for academic report.
Creates:
  1. figures/system_architecture.png
  2. figures/market_trends.png
"""

from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import pandas as pd
import numpy as np

FIGURES_DIR = Path("figures")
FIGURES_DIR.mkdir(parents=True, exist_ok=True)


def generate_architecture_diagram():
    fig, ax = plt.subplots(figsize=(10, 5), dpi=200)
    ax.axis("off")

    # Define color scheme
    c_data = "#E3F2FD"
    c_ml = "#E8F5E9"
    c_app = "#FFF3E0"
    edge_color = "#37474F"

    # Box dimensions
    bw, bh = 2.4, 1.1

    # Stage 1: Data Pipeline
    ax.text(1.5, 4.5, "Stage 1: Data Ingestion & Hygiene", fontsize=11, fontweight="bold", ha="center", color="#1565C0")
    b1 = patches.FancyBboxPatch((0.3, 2.9), bw, bh, boxstyle="round,pad=0.1", fc=c_data, ec="#1976D2", lw=1.5)
    ax.add_patch(b1)
    ax.text(1.5, 3.45, "Raw Postings (15,000+)\n• Exact & Near-Dedup\n• HTML & Text Sanitization", ha="center", va="center", fontsize=8.5)

    b2 = patches.FancyBboxPatch((0.3, 1.2), bw, bh, boxstyle="round,pad=0.1", fc=c_data, ec="#1976D2", lw=1.5)
    ax.add_patch(b2)
    ax.text(1.5, 1.75, "Chronological Split\n• 70% Train (Pre-2024)\n• 15% Val / 15% Test", ha="center", va="center", fontsize=8.5)

    # Stage 2: Feature & Modeling
    ax.text(5.0, 4.5, "Stage 2: Machine Learning Pipeline", fontsize=11, fontweight="bold", ha="center", color="#2E7D32")
    b3 = patches.FancyBboxPatch((3.8, 2.9), bw, bh, boxstyle="round,pad=0.1", fc=c_ml, ec="#388E3C", lw=1.5)
    ax.add_patch(b3)
    ax.text(5.0, 3.45, "Feature Engineering\n• 4,818 TF-IDF n-grams\n• 10 Structured Meta Features", ha="center", va="center", fontsize=8.5)

    b4 = patches.FancyBboxPatch((3.8, 1.2), bw, bh, boxstyle="round,pad=0.1", fc=c_ml, ec="#388E3C", lw=1.5)
    ax.add_patch(b4)
    ax.text(5.0, 1.75, "Model Benchmark & Selection\n• 5 Models (Dummy to LightGBM)\n• Selection: Macro F1-Score", ha="center", va="center", fontsize=8.5)

    # Stage 3: Application Services
    ax.text(8.5, 4.5, "Stage 3: Interactive UI & Roadmaps", fontsize=11, fontweight="bold", ha="center", color="#E65100")
    b5 = patches.FancyBboxPatch((7.3, 2.9), bw, bh, boxstyle="round,pad=0.1", fc=c_app, ec="#F57C00", lw=1.5)
    ax.add_patch(b5)
    ax.text(8.5, 3.45, "Profile Match Engine\n• 55% Skill / 30% Exp Fit\n• Transparent Score (0-100)", ha="center", va="center", fontsize=8.5)

    b6 = patches.FancyBboxPatch((7.3, 1.2), bw, bh, boxstyle="round,pad=0.1", fc=c_app, ec="#F57C00", lw=1.5)
    ax.add_patch(b6)
    ax.text(8.5, 1.75, "Personalized Roadmap\n• Stage-based Pathways\n• Verified roadmap.sh Links", ha="center", va="center", fontsize=8.5)

    # Connectors
    arrows = [
        ((1.5, 2.9), (1.5, 2.3)),
        ((2.7, 1.75), (3.8, 1.75)),
        ((5.0, 2.9), (5.0, 2.3)),
        ((2.7, 3.45), (3.8, 3.45)),
        ((6.2, 3.45), (7.3, 3.45)),
        ((6.2, 1.75), (7.3, 1.75)),
        ((8.5, 2.9), (8.5, 2.3)),
    ]
    for start, end in arrows:
        ax.annotate("", xy=end, xytext=start, arrowprops=dict(arrowstyle="->", lw=1.5, color="#546E7A"))

    ax.set_xlim(0, 10)
    ax.set_ylim(0.5, 5.0)
    plt.tight_layout()
    out = FIGURES_DIR / "system_architecture.png"
    plt.savefig(out, dpi=200, bbox_inches="tight")
    plt.close()
    print("Saved:", out)


def generate_market_trends_figure():
    df_clean_path = Path("data/processed/jobs_clean.csv")
    if not df_clean_path.exists():
        print("jobs_clean.csv not found")
        return
    df = pd.read_csv(df_clean_path)

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2), dpi=200)

    # Top domains
    domain_counts = df["domain"].value_counts().head(7)
    axes[0].barh(domain_counts.index, domain_counts.values, color="#1976D2", alpha=0.85)
    axes[0].set_xlabel("Number of Observable Postings", fontsize=9)
    axes[0].set_title("Recruitment Demand by Technical Domain (2023–2024)", fontsize=10, fontweight="bold")
    axes[0].grid(axis="x", alpha=0.3)
    axes[0].invert_yaxis()

    # Top skills
    skills_series = df["skills_required"].dropna().str.split("|").explode().str.strip()
    top_skills = skills_series.value_counts().head(10)
    axes[1].barh(top_skills.index, top_skills.values, color="#388E3C", alpha=0.85)
    axes[1].set_xlabel("Skill Frequency Across Postings", fontsize=9)
    axes[1].set_title("Top 10 In-Demand Technical Skills", fontsize=10, fontweight="bold")
    axes[1].grid(axis="x", alpha=0.3)
    axes[1].invert_yaxis()

    plt.tight_layout()
    out = FIGURES_DIR / "market_trends.png"
    plt.savefig(out, dpi=200, bbox_inches="tight")
    plt.close()
    print("Saved:", out)


if __name__ == "__main__":
    generate_architecture_diagram()
    generate_market_trends_figure()
