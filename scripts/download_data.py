"""
CareerPulse — Dataset acquisition script.

Downloads the LinkedIn Job Postings (2023-2024) dataset from Kaggle.
Dataset: https://www.kaggle.com/datasets/arshkon/linkedin-job-postings
Publisher: Arsh Koneru
License: Open Database License (ODbL)
Access date: 2026-10-22

Usage:
    1. Install Kaggle CLI: pip install kaggle
    2. Place your Kaggle API token at ~/.kaggle/kaggle.json
       (Download from https://www.kaggle.com/settings > API > Create New Token)
    3. Run: python scripts/download_data.py

Records: ~124,000+ job postings
Fields: job_id, title, company_id, description, formatted_experience_level,
        location, work_type, listed_time, salary info, skills, company details
"""

import os
import sys
import zipfile
import subprocess
from pathlib import Path

RAW_DIR = Path("data/raw")
KAGGLE_DATASET = "arshkon/linkedin-job-postings"


def check_kaggle_credentials():
    """Verify that Kaggle API credentials are present."""
    kaggle_json = Path.home() / ".kaggle" / "kaggle.json"
    if not kaggle_json.exists():
        print("ERROR: Kaggle API token not found.")
        print(f"  Expected at: {kaggle_json}")
        print("  Steps to fix:")
        print("    1. Go to https://www.kaggle.com/settings")
        print("    2. Under 'API', click 'Create New Token'")
        print("    3. Save the downloaded kaggle.json to ~/.kaggle/kaggle.json")
        return False
    return True


def download_dataset():
    """Download and extract the LinkedIn job postings dataset."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    if not check_kaggle_credentials():
        sys.exit(1)

    print(f"Downloading {KAGGLE_DATASET} to {RAW_DIR}/...")
    result = subprocess.run(
        ["kaggle", "datasets", "download", "-d", KAGGLE_DATASET,
         "-p", str(RAW_DIR), "--unzip"],
        capture_output=True, text=True
    )

    if result.returncode != 0:
        print(f"Download failed:\n{result.stderr}")
        sys.exit(1)

    print("Download complete. Verifying files...")
    expected_files = [
        "job_postings.csv",
        "companies.csv",
        "skills.csv",
    ]
    for f in expected_files:
        fp = RAW_DIR / f
        if fp.exists():
            size_mb = fp.stat().st_size / 1_048_576
            print(f"  ✓ {f} ({size_mb:.1f} MB)")
        else:
            print(f"  ✗ {f} NOT FOUND")

    print("\nDataset metadata:")
    print("  Source:   https://www.kaggle.com/datasets/arshkon/linkedin-job-postings")
    print("  Publisher: Arsh Koneru")
    print("  License:  Open Database License (ODbL)")
    print("  Coverage: 2023–2024 LinkedIn job postings")
    print("  Unit:     Individual job posting")


if __name__ == "__main__":
    download_dataset()
