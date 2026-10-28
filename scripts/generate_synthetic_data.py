"""
CareerPulse — Synthetic dataset generator.

Since Kaggle credentials are required for the real LinkedIn dataset,
this script generates a realistic synthetic dataset that mirrors the
schema and statistical properties of the LinkedIn Job Postings (2023-2024)
dataset published by Arsh Koneru at:
  https://www.kaggle.com/datasets/arshkon/linkedin-job-postings

The generated data is NOT real job postings. It is used for reproducible
academic experimentation when the original dataset cannot be downloaded.

This approach is documented as a limitation in the project report.
"""

import numpy as np
import pandas as pd
from pathlib import Path
import random
from datetime import datetime, timedelta

RANDOM_SEED = 42
np.random.seed(RANDOM_SEED)
random.seed(RANDOM_SEED)

RAW_DIR = Path("data/raw")
RAW_DIR.mkdir(parents=True, exist_ok=True)

# ─── Domain / role / skill taxonomy ─────────────────────────────────────────

DOMAINS = {
    "Data Science": {
        "titles": [
            "Data Scientist", "Senior Data Scientist", "Lead Data Scientist",
            "Junior Data Scientist", "Principal Data Scientist",
            "Applied Data Scientist", "Staff Data Scientist"
        ],
        "skills": [
            "Python", "R", "SQL", "Machine Learning", "Deep Learning",
            "TensorFlow", "PyTorch", "Scikit-learn", "Pandas", "NumPy",
            "Statistics", "Data Visualization", "Tableau", "Power BI",
            "Spark", "Hadoop", "A/B Testing", "Feature Engineering",
            "Natural Language Processing", "Computer Vision", "MLflow",
            "Jupyter", "Git", "Docker", "Kubernetes"
        ],
    },
    "Machine Learning": {
        "titles": [
            "Machine Learning Engineer", "Senior ML Engineer",
            "ML Research Scientist", "Applied ML Engineer",
            "MLOps Engineer", "AI Engineer", "Research Engineer"
        ],
        "skills": [
            "Python", "TensorFlow", "PyTorch", "Scikit-learn",
            "MLflow", "Kubeflow", "Docker", "Kubernetes", "AWS SageMaker",
            "Google Vertex AI", "Model Deployment", "Feature Engineering",
            "Data Pipeline", "SQL", "Spark", "CUDA", "Git",
            "FastAPI", "REST APIs", "CI/CD", "Cloud Computing",
            "Natural Language Processing", "Computer Vision", "LLMs",
        ],
    },
    "Software Development": {
        "titles": [
            "Software Engineer", "Senior Software Engineer",
            "Software Developer", "Backend Engineer", "Full Stack Engineer",
            "Junior Software Engineer", "Staff Engineer", "Principal Engineer"
        ],
        "skills": [
            "Python", "Java", "C++", "JavaScript", "TypeScript",
            "React", "Node.js", "Spring Boot", "Django", "FastAPI",
            "SQL", "NoSQL", "MongoDB", "PostgreSQL", "Redis",
            "Docker", "Kubernetes", "AWS", "GCP", "Azure",
            "Git", "CI/CD", "Agile", "REST APIs", "GraphQL",
            "Microservices", "Linux", "System Design"
        ],
    },
    "Data Engineering": {
        "titles": [
            "Data Engineer", "Senior Data Engineer", "Lead Data Engineer",
            "Analytics Engineer", "Platform Engineer", "ETL Developer",
            "Data Infrastructure Engineer"
        ],
        "skills": [
            "Python", "SQL", "Spark", "Airflow", "Kafka",
            "dbt", "Snowflake", "BigQuery", "Redshift", "S3",
            "Hadoop", "Hive", "Databricks", "ETL", "ELT",
            "Docker", "Kubernetes", "Terraform", "AWS", "GCP",
            "Azure", "Git", "Data Modeling", "CI/CD", "Linux"
        ],
    },
    "Cybersecurity": {
        "titles": [
            "Security Engineer", "Cybersecurity Analyst", "SOC Analyst",
            "Penetration Tester", "Information Security Engineer",
            "Cloud Security Engineer", "Security Architect"
        ],
        "skills": [
            "Network Security", "Penetration Testing", "SIEM", "SOAR",
            "Firewalls", "IDS/IPS", "Vulnerability Assessment", "Python",
            "Linux", "Windows Security", "Cloud Security", "AWS",
            "Azure Security", "OWASP", "Incident Response", "Forensics",
            "Cryptography", "Zero Trust", "Identity Management", "CISSP",
            "CEH", "CompTIA Security+", "Git", "Splunk", "Wireshark"
        ],
    },
    "Cloud Computing": {
        "titles": [
            "Cloud Engineer", "Cloud Architect", "DevOps Engineer",
            "Site Reliability Engineer", "Cloud Solutions Architect",
            "Infrastructure Engineer", "Platform Engineer"
        ],
        "skills": [
            "AWS", "GCP", "Azure", "Terraform", "Ansible",
            "Docker", "Kubernetes", "CI/CD", "Linux", "Python",
            "Bash", "CloudFormation", "Infrastructure as Code",
            "Monitoring", "Logging", "Networking", "Load Balancing",
            "Serverless", "Lambda", "Microservices", "Git", "Jenkins",
            "GitHub Actions", "Cost Optimization", "Security"
        ],
    },
    "Web Development": {
        "titles": [
            "Frontend Developer", "Backend Developer", "Full Stack Developer",
            "Web Developer", "Senior Frontend Developer",
            "React Developer", "Angular Developer", "Vue.js Developer"
        ],
        "skills": [
            "HTML", "CSS", "JavaScript", "TypeScript", "React",
            "Angular", "Vue.js", "Node.js", "Express.js", "Next.js",
            "SQL", "MongoDB", "REST APIs", "GraphQL", "Git",
            "CSS Frameworks", "Tailwind CSS", "Webpack", "Vite",
            "Testing", "Jest", "CI/CD", "Docker", "AWS",
            "Performance Optimization", "Responsive Design", "Accessibility"
        ],
    },
}

COMPANIES = [
    ("Google", "Technology", "Sunnyvale, CA"),
    ("Microsoft", "Technology", "Redmond, WA"),
    ("Amazon", "Technology", "Seattle, WA"),
    ("Meta", "Technology", "Menlo Park, CA"),
    ("Apple", "Technology", "Cupertino, CA"),
    ("Netflix", "Entertainment", "Los Gatos, CA"),
    ("Salesforce", "Cloud Software", "San Francisco, CA"),
    ("IBM", "Technology", "Armonk, NY"),
    ("Oracle", "Enterprise Software", "Austin, TX"),
    ("Cisco", "Networking", "San Jose, CA"),
    ("Intel", "Semiconductors", "Santa Clara, CA"),
    ("NVIDIA", "Semiconductors", "Santa Clara, CA"),
    ("Adobe", "Creative Software", "San Jose, CA"),
    ("LinkedIn", "Professional Network", "Sunnyvale, CA"),
    ("Uber", "Transportation Tech", "San Francisco, CA"),
    ("Airbnb", "Travel Tech", "San Francisco, CA"),
    ("Stripe", "Fintech", "San Francisco, CA"),
    ("Snowflake", "Cloud Data", "Bozeman, MT"),
    ("Databricks", "Data AI", "San Francisco, CA"),
    ("Palantir", "Data Analytics", "Denver, CO"),
    ("Crowdstrike", "Cybersecurity", "Austin, TX"),
    ("Palo Alto Networks", "Cybersecurity", "Santa Clara, CA"),
    ("Cloudflare", "Internet Security", "San Francisco, CA"),
    ("Okta", "Identity Security", "San Francisco, CA"),
    ("ServiceNow", "IT Management", "Santa Clara, CA"),
    ("Workday", "HR Software", "Pleasanton, CA"),
    ("Zoom", "Communications", "San Jose, CA"),
    ("Slack", "Collaboration", "San Francisco, CA"),
    ("Dropbox", "Cloud Storage", "San Francisco, CA"),
    ("Twilio", "Communications API", "San Francisco, CA"),
    ("Datadog", "Monitoring", "New York, NY"),
    ("HashiCorp", "Infrastructure", "San Francisco, CA"),
    ("Confluent", "Data Streaming", "Mountain View, CA"),
    ("MongoDB", "Database", "New York, NY"),
    ("Elastic", "Search Analytics", "Mountain View, CA"),
    ("JPMorgan Chase", "Finance", "New York, NY"),
    ("Goldman Sachs", "Finance", "New York, NY"),
    ("Capital One", "Fintech", "McLean, VA"),
    ("Spotify", "Music Tech", "New York, NY"),
    ("Twitter/X", "Social Media", "San Francisco, CA"),
]

EXPERIENCE_LEVELS = {
    "Entry level": {"years": (0, 2), "weight": 0.25},
    "Associate":   {"years": (1, 3), "weight": 0.20},
    "Mid-Senior level": {"years": (3, 7), "weight": 0.30},
    "Senior":      {"years": (5, 10), "weight": 0.15},
    "Director":    {"years": (8, 15), "weight": 0.05},
    "Executive":   {"years": (12, 25), "weight": 0.05},
}

WORK_TYPES = ["Full-time", "Part-time", "Contract", "Temporary", "Internship"]
WORK_TYPE_WEIGHTS = [0.70, 0.05, 0.15, 0.05, 0.05]

LOCATIONS = [
    "San Francisco, CA", "New York, NY", "Seattle, WA", "Austin, TX",
    "Los Angeles, CA", "Boston, MA", "Chicago, IL", "Atlanta, GA",
    "Denver, CO", "Washington, DC", "Remote", "Hybrid - San Francisco, CA",
    "Hybrid - New York, NY", "Hybrid - Seattle, WA", "Dallas, TX",
    "San Jose, CA", "Sunnyvale, CA", "Mountain View, CA", "Redmond, WA",
    "Menlo Park, CA", "Cambridge, MA", "Raleigh, NC", "Portland, OR",
]

SALARY_RANGES_BY_LEVEL = {
    "Entry level":      (60_000, 95_000),
    "Associate":        (75_000, 110_000),
    "Mid-Senior level": (100_000, 160_000),
    "Senior":           (140_000, 220_000),
    "Director":         (180_000, 300_000),
    "Executive":        (250_000, 500_000),
}


def generate_job_description(domain, title, skills_required, exp_level):
    """Generate a realistic job description."""
    intro_templates = [
        f"We are looking for a talented {title} to join our growing team.",
        f"Join us as a {title} and help shape the future of technology.",
        f"We're hiring an experienced {title} to drive innovation.",
        f"Exciting opportunity for a {title} to make a real impact.",
    ]
    skill_str = ", ".join(skills_required[:5])
    years_range = EXPERIENCE_LEVELS[exp_level]["years"]
    years_text = f"{years_range[0]}-{years_range[1]} years"

    desc = (
        f"{random.choice(intro_templates)}\n\n"
        f"**About the Role:**\n"
        f"As a {title}, you will work on cutting-edge {domain} projects, "
        f"collaborate with cross-functional teams, and deliver high-quality solutions. "
        f"This role requires strong expertise in {skill_str}.\n\n"
        f"**Requirements:**\n"
        f"- {years_text} of experience in {domain}\n"
        f"- Proficiency in {', '.join(skills_required[:4])}\n"
        f"- Experience with {', '.join(skills_required[4:8]) if len(skills_required) > 4 else skill_str}\n"
        f"- Strong problem-solving and communication skills\n"
        f"- Bachelor's or Master's degree in Computer Science or related field\n\n"
        f"**Nice to Have:**\n"
        f"- Experience with {', '.join(skills_required[8:12]) if len(skills_required) > 8 else 'cloud platforms'}\n"
        f"- Contributions to open-source projects\n"
        f"- Experience in Agile/Scrum environments\n\n"
        f"**What We Offer:**\n"
        f"- Competitive salary and equity\n"
        f"- Health, dental, and vision insurance\n"
        f"- Flexible work arrangements\n"
        f"- Professional development budget\n"
    )
    return desc


def generate_dataset(n_records: int = 15000) -> None:
    """Generate synthetic job postings dataset."""
    print(f"Generating {n_records} synthetic job postings...")

    records = []
    domain_names = list(DOMAINS.keys())
    exp_levels = list(EXPERIENCE_LEVELS.keys())
    exp_weights = [v["weight"] for v in EXPERIENCE_LEVELS.values()]

    start_date = datetime(2023, 1, 1)
    end_date = datetime(2024, 12, 31)
    date_range_days = (end_date - start_date).days

    company_list = COMPANIES.copy()

    for i in range(n_records):
        domain = random.choice(domain_names)
        domain_info = DOMAINS[domain]
        title = random.choice(domain_info["titles"])

        # Skills: pick 6-14 required, 2-4 nice-to-have
        all_skills = domain_info["skills"]
        n_req = random.randint(6, min(14, len(all_skills)))
        skills_chosen = random.sample(all_skills, n_req)

        exp_level = random.choices(exp_levels, weights=exp_weights, k=1)[0]

        company_tuple = random.choice(company_list)
        company_name, industry, company_hq = company_tuple
        company_id = company_list.index(company_tuple) + 1

        location = random.choice(LOCATIONS)
        work_type = random.choices(WORK_TYPES, weights=WORK_TYPE_WEIGHTS, k=1)[0]

        # Posting date
        post_offset = random.randint(0, date_range_days)
        post_date = start_date + timedelta(days=post_offset)

        # Salary (30% missing)
        sal_range = SALARY_RANGES_BY_LEVEL[exp_level]
        has_salary = random.random() > 0.30
        if has_salary:
            sal_min = random.randint(sal_range[0], int(sal_range[1] * 0.8))
            sal_max = random.randint(sal_min, sal_range[1])
            sal_currency = "USD"
            sal_period = "YEARLY"
        else:
            sal_min = sal_max = np.nan
            sal_currency = np.nan
            sal_period = np.nan

        description = generate_job_description(domain, title, skills_chosen, exp_level)

        # Simulate some data quality issues
        if random.random() < 0.03:  # 3% missing experience level
            exp_level_field = np.nan
        else:
            exp_level_field = exp_level

        if random.random() < 0.05:  # 5% missing location
            location_field = np.nan
        else:
            location_field = location

        records.append({
            "job_id": 1000000 + i,
            "company_id": company_id,
            "title": title,
            "description": description,
            "formatted_experience_level": exp_level_field,
            "location": location_field,
            "work_type": work_type,
            "listed_time": post_date.strftime("%Y-%m-%d %H:%M:%S"),
            "domain": domain,
            "skills_required": "|".join(skills_chosen),
            "min_salary": sal_min,
            "max_salary": sal_max,
            "currency": sal_currency,
            "compensation_type": sal_period,
            "applies": random.randint(10, 5000),
            "remote_allowed": int("Remote" in location or "Hybrid" in location),
            "views": random.randint(100, 50000),
        })

    df = pd.DataFrame(records)

    # Introduce 50 intentional duplicates
    dup_indices = np.random.choice(len(df), size=50, replace=False)
    dups = df.iloc[dup_indices].copy()
    df = pd.concat([df, dups], ignore_index=True)
    df = df.sample(frac=1, random_state=RANDOM_SEED).reset_index(drop=True)

    # Save job postings
    df.to_csv(RAW_DIR / "job_postings.csv", index=False)
    print(f"  Saved job_postings.csv: {len(df)} rows, {df.shape[1]} columns")

    # Generate companies.csv
    companies_df = pd.DataFrame([
        {
            "company_id": i + 1,
            "name": c[0],
            "description": f"{c[0]} is a leading company in the {c[1]} industry.",
            "company_size": random.choice([
                "1-10", "11-50", "51-200", "201-500",
                "501-1000", "1001-5000", "5001-10000", "10001+"
            ]),
            "headquarters": c[2],
            "follower_count": random.randint(1000, 5_000_000),
            "employee_count": random.randint(50, 200_000),
            "industry": c[1],
        }
        for i, c in enumerate(COMPANIES)
    ])
    companies_df.to_csv(RAW_DIR / "companies.csv", index=False)
    print(f"  Saved companies.csv: {len(companies_df)} rows")

    # Generate skills.csv (long-form: one row per job-skill pair)
    skills_rows = []
    for _, row in df.iterrows():
        if pd.notna(row["skills_required"]):
            for skill in str(row["skills_required"]).split("|"):
                skills_rows.append({"job_id": row["job_id"], "skill_abr": skill.strip()})
    skills_df = pd.DataFrame(skills_rows)
    skills_df.to_csv(RAW_DIR / "skills.csv", index=False)
    print(f"  Saved skills.csv: {len(skills_df)} rows")

    # Metadata
    meta = {
        "source": "Synthetic dataset modelling LinkedIn Job Postings (2023-2024) by Arsh Koneru",
        "original_url": "https://www.kaggle.com/datasets/arshkon/linkedin-job-postings",
        "license": "For academic use only — synthetic data, not real LinkedIn data",
        "generation_date": datetime.now().strftime("%Y-%m-%d"),
        "n_postings": len(df),
        "n_companies": len(companies_df),
        "date_coverage": "2023-01-01 to 2024-12-31",
        "note": (
            "Kaggle credentials were not available during generation. "
            "This synthetic dataset mirrors the schema and approximate statistical "
            "distribution of the original dataset. Results will differ from the real dataset."
        ),
    }
    import json
    with open(RAW_DIR / "dataset_metadata.json", "w") as f:
        json.dump(meta, f, indent=2)
    print("  Saved dataset_metadata.json")
    print("\nDataset generation complete.")


if __name__ == "__main__":
    generate_dataset(n_records=15000)
