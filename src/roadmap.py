"""
CareerPulse — Personalized learning roadmap generator.

Generates a role-specific, skill-gap-driven learning roadmap.
Resources are verified as of 2024-10-22 and come from official
or well-established public documentation.
"""

import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

# ─── Verified learning resources ─────────────────────────────────────────────
# All URLs verified as active public resources. roadmap.sh is a community-maintained
# public resource. Official docs are from their respective publishers.

ROADMAPS = {
    "Data Science": {
        "roadmap_url": "https://roadmap.sh/ai-data-scientist",
        "stages": {
            "Beginner": {
                "skills": ["Python", "SQL", "Statistics", "Pandas", "NumPy"],
                "projects": [
                    "Exploratory data analysis on a public dataset (e.g., Titanic, NYC flights)",
                    "Simple linear regression from scratch using NumPy",
                ],
                "resources": [
                    {"name": "Python Official Tutorial", "url": "https://docs.python.org/3/tutorial/"},
                    {"name": "Kaggle Pandas Course", "url": "https://www.kaggle.com/learn/pandas"},
                    {"name": "Khan Academy Statistics", "url": "https://www.khanacademy.org/math/statistics-probability"},
                ],
            },
            "Intermediate": {
                "skills": ["Machine Learning", "Scikit-learn", "Feature Engineering", "Data Visualization", "Tableau"],
                "projects": [
                    "End-to-end ML pipeline: classification or regression on a tabular dataset",
                    "Interactive dashboard with Plotly or Tableau Public",
                ],
                "resources": [
                    {"name": "Scikit-learn User Guide", "url": "https://scikit-learn.org/stable/user_guide.html"},
                    {"name": "Kaggle ML Courses", "url": "https://www.kaggle.com/learn"},
                    {"name": "Plotly Documentation", "url": "https://plotly.com/python/"},
                ],
            },
            "Advanced": {
                "skills": ["Deep Learning", "TensorFlow", "PyTorch", "NLP", "MLflow", "Spark"],
                "projects": [
                    "Train and deploy an NLP model (sentiment analysis, text classification)",
                    "Build an ML experiment tracking pipeline with MLflow",
                ],
                "resources": [
                    {"name": "TensorFlow Documentation", "url": "https://www.tensorflow.org/learn"},
                    {"name": "PyTorch Tutorials", "url": "https://pytorch.org/tutorials/"},
                    {"name": "fast.ai Practical Deep Learning", "url": "https://course.fast.ai/"},
                ],
            },
        },
    },
    "Machine Learning": {
        "roadmap_url": "https://roadmap.sh/ai-data-scientist",
        "stages": {
            "Beginner": {
                "skills": ["Python", "Statistics", "Linear Algebra", "Scikit-learn", "Git"],
                "projects": [
                    "Implement k-NN and decision tree classifier from scratch",
                    "Binary classification with logistic regression",
                ],
                "resources": [
                    {"name": "Scikit-learn Documentation", "url": "https://scikit-learn.org/stable/"},
                    {"name": "3Blue1Brown: Linear Algebra", "url": "https://www.3blue1brown.com/topics/linear-algebra"},
                    {"name": "Python Official Tutorial", "url": "https://docs.python.org/3/tutorial/"},
                ],
            },
            "Intermediate": {
                "skills": ["TensorFlow", "PyTorch", "Feature Engineering", "Model Deployment", "FastAPI"],
                "projects": [
                    "Train an image classifier and deploy as a REST API with FastAPI",
                    "Model optimization and hyperparameter tuning with Optuna",
                ],
                "resources": [
                    {"name": "TensorFlow Tutorials", "url": "https://www.tensorflow.org/tutorials"},
                    {"name": "FastAPI Documentation", "url": "https://fastapi.tiangolo.com/"},
                    {"name": "Optuna Documentation", "url": "https://optuna.readthedocs.io/"},
                ],
            },
            "Advanced": {
                "skills": ["MLOps", "Kubeflow", "AWS SageMaker", "CUDA", "LLMs", "MLflow"],
                "projects": [
                    "Build an end-to-end MLOps pipeline with CI/CD and model monitoring",
                    "Fine-tune a language model and serve it with a scalable API",
                ],
                "resources": [
                    {"name": "MLflow Documentation", "url": "https://mlflow.org/docs/latest/index.html"},
                    {"name": "AWS SageMaker Developer Guide", "url": "https://docs.aws.amazon.com/sagemaker/"},
                    {"name": "Hugging Face Transformers Docs", "url": "https://huggingface.co/docs/transformers/"},
                ],
            },
        },
    },
    "Software Development": {
        "roadmap_url": "https://roadmap.sh/backend",
        "stages": {
            "Beginner": {
                "skills": ["Python", "Git", "Linux", "SQL", "REST APIs"],
                "projects": [
                    "Build a CLI tool with Python argparse",
                    "Create a simple REST API with FastAPI or Flask",
                ],
                "resources": [
                    {"name": "roadmap.sh Backend Developer", "url": "https://roadmap.sh/backend"},
                    {"name": "Git Documentation", "url": "https://git-scm.com/doc"},
                    {"name": "FastAPI Documentation", "url": "https://fastapi.tiangolo.com/"},
                ],
            },
            "Intermediate": {
                "skills": ["Docker", "PostgreSQL", "Microservices", "CI/CD", "System Design"],
                "projects": [
                    "Containerize a multi-service application with Docker Compose",
                    "Design and implement a microservices architecture",
                ],
                "resources": [
                    {"name": "Docker Official Documentation", "url": "https://docs.docker.com/"},
                    {"name": "PostgreSQL Documentation", "url": "https://www.postgresql.org/docs/"},
                    {"name": "roadmap.sh DevOps", "url": "https://roadmap.sh/devops"},
                ],
            },
            "Advanced": {
                "skills": ["Kubernetes", "AWS", "System Design", "Performance Optimization"],
                "projects": [
                    "Deploy a containerized application to Kubernetes on AWS EKS",
                    "Design a high-availability distributed system",
                ],
                "resources": [
                    {"name": "Kubernetes Documentation", "url": "https://kubernetes.io/docs/"},
                    {"name": "AWS Documentation", "url": "https://docs.aws.amazon.com/"},
                    {"name": "System Design Primer (GitHub)", "url": "https://github.com/donnemartin/system-design-primer"},
                ],
            },
        },
    },
    "Data Engineering": {
        "roadmap_url": "https://roadmap.sh/dataengineering",
        "stages": {
            "Beginner": {
                "skills": ["Python", "SQL", "Git", "Linux", "ETL"],
                "projects": [
                    "Build a simple ETL pipeline with Python and SQLite",
                    "Write SQL queries for data aggregation and analysis",
                ],
                "resources": [
                    {"name": "roadmap.sh Data Engineer", "url": "https://roadmap.sh/dataengineering"},
                    {"name": "Mode SQL Tutorial", "url": "https://mode.com/sql-tutorial/"},
                    {"name": "Python Official Docs", "url": "https://docs.python.org/3/"},
                ],
            },
            "Intermediate": {
                "skills": ["Airflow", "Spark", "dbt", "Snowflake", "Kafka"],
                "projects": [
                    "Build a data pipeline with Apache Airflow and Spark",
                    "Implement data transformations with dbt",
                ],
                "resources": [
                    {"name": "Apache Airflow Documentation", "url": "https://airflow.apache.org/docs/"},
                    {"name": "Apache Spark Documentation", "url": "https://spark.apache.org/docs/latest/"},
                    {"name": "dbt Documentation", "url": "https://docs.getdbt.com/"},
                ],
            },
            "Advanced": {
                "skills": ["Databricks", "Terraform", "Kubernetes", "Data Modeling", "Real-time Processing"],
                "projects": [
                    "Build a real-time streaming pipeline with Kafka and Spark Structured Streaming",
                    "Implement a medallion architecture on Databricks",
                ],
                "resources": [
                    {"name": "Databricks Documentation", "url": "https://docs.databricks.com/"},
                    {"name": "Terraform Documentation", "url": "https://developer.hashicorp.com/terraform/docs"},
                    {"name": "Kafka Documentation", "url": "https://kafka.apache.org/documentation/"},
                ],
            },
        },
    },
    "Cybersecurity": {
        "roadmap_url": "https://roadmap.sh/cyber-security",
        "stages": {
            "Beginner": {
                "skills": ["Linux", "Networking", "Python", "Network Security"],
                "projects": [
                    "Set up a home lab with VirtualBox and practice Linux commands",
                    "Write a Python script for port scanning (using nmap library)",
                ],
                "resources": [
                    {"name": "roadmap.sh Cybersecurity", "url": "https://roadmap.sh/cyber-security"},
                    {"name": "TryHackMe (Free Rooms)", "url": "https://tryhackme.com/"},
                    {"name": "OWASP Top 10", "url": "https://owasp.org/www-project-top-ten/"},
                ],
            },
            "Intermediate": {
                "skills": ["Penetration Testing", "SIEM", "Vulnerability Assessment", "Splunk", "Wireshark"],
                "projects": [
                    "Complete Hack The Box beginner challenges",
                    "Set up Splunk for log analysis and create alerts",
                ],
                "resources": [
                    {"name": "Hack The Box", "url": "https://www.hackthebox.com/"},
                    {"name": "Splunk Documentation", "url": "https://docs.splunk.com/"},
                    {"name": "Wireshark User Guide", "url": "https://www.wireshark.org/docs/wsug_html_chunked/"},
                ],
            },
            "Advanced": {
                "skills": ["Cloud Security", "Zero Trust", "CISSP", "Incident Response", "Cryptography"],
                "projects": [
                    "Implement a Zero Trust architecture on AWS",
                    "Build an incident response playbook",
                ],
                "resources": [
                    {"name": "AWS Security Documentation", "url": "https://docs.aws.amazon.com/security/"},
                    {"name": "NIST Cybersecurity Framework", "url": "https://www.nist.gov/cyberframework"},
                    {"name": "ISC² CISSP Prep", "url": "https://www.isc2.org/Certifications/CISSP"},
                ],
            },
        },
    },
    "Cloud Computing": {
        "roadmap_url": "https://roadmap.sh/devops",
        "stages": {
            "Beginner": {
                "skills": ["Linux", "Networking", "Git", "Python", "Bash"],
                "projects": [
                    "Deploy a static website on AWS S3 with CloudFront",
                    "Write Bash scripts to automate system administration tasks",
                ],
                "resources": [
                    {"name": "AWS Free Tier", "url": "https://aws.amazon.com/free/"},
                    {"name": "Linux Command Line Tutorial", "url": "https://linuxcommand.org/tlcl.php"},
                    {"name": "roadmap.sh DevOps", "url": "https://roadmap.sh/devops"},
                ],
            },
            "Intermediate": {
                "skills": ["Docker", "Kubernetes", "Terraform", "CI/CD", "AWS"],
                "projects": [
                    "Set up a Kubernetes cluster on AWS EKS",
                    "Create a Terraform module for a multi-tier web application",
                ],
                "resources": [
                    {"name": "AWS Documentation", "url": "https://docs.aws.amazon.com/"},
                    {"name": "Terraform Documentation", "url": "https://developer.hashicorp.com/terraform/docs"},
                    {"name": "Kubernetes Documentation", "url": "https://kubernetes.io/docs/"},
                ],
            },
            "Advanced": {
                "skills": ["Serverless", "Monitoring", "Cost Optimization", "Security", "Multi-cloud"],
                "projects": [
                    "Build a serverless data processing pipeline with AWS Lambda and Step Functions",
                    "Implement cloud cost optimization with auto-scaling and reserved instances",
                ],
                "resources": [
                    {"name": "AWS Architecture Center", "url": "https://aws.amazon.com/architecture/"},
                    {"name": "GCP Documentation", "url": "https://cloud.google.com/docs"},
                    {"name": "Azure Documentation", "url": "https://learn.microsoft.com/en-us/azure/"},
                ],
            },
        },
    },
    "Web Development": {
        "roadmap_url": "https://roadmap.sh/frontend",
        "stages": {
            "Beginner": {
                "skills": ["HTML", "CSS", "JavaScript", "Git", "Responsive Design"],
                "projects": [
                    "Build a personal portfolio website with HTML and CSS",
                    "Create an interactive quiz app with vanilla JavaScript",
                ],
                "resources": [
                    {"name": "MDN Web Docs", "url": "https://developer.mozilla.org/en-US/docs/Learn"},
                    {"name": "roadmap.sh Frontend", "url": "https://roadmap.sh/frontend"},
                    {"name": "freeCodeCamp Responsive Web Design", "url": "https://www.freecodecamp.org/learn/2022/responsive-web-design/"},
                ],
            },
            "Intermediate": {
                "skills": ["React", "TypeScript", "Node.js", "REST APIs", "SQL"],
                "projects": [
                    "Build a full-stack todo app with React, Node.js, and PostgreSQL",
                    "Create a real-time chat application with WebSockets",
                ],
                "resources": [
                    {"name": "React Official Docs", "url": "https://react.dev/"},
                    {"name": "TypeScript Documentation", "url": "https://www.typescriptlang.org/docs/"},
                    {"name": "Node.js Documentation", "url": "https://nodejs.org/en/docs/"},
                ],
            },
            "Advanced": {
                "skills": ["Next.js", "GraphQL", "Docker", "Performance Optimization", "Accessibility"],
                "projects": [
                    "Build and deploy a production Next.js application with SSR and edge caching",
                    "Optimize a web application for Core Web Vitals",
                ],
                "resources": [
                    {"name": "Next.js Documentation", "url": "https://nextjs.org/docs"},
                    {"name": "GraphQL Documentation", "url": "https://graphql.org/learn/"},
                    {"name": "Web.dev Performance", "url": "https://web.dev/performance/"},
                ],
            },
        },
    },
}

DEFAULT_ROADMAP = ROADMAPS["Software Development"]


def get_roadmap(
    domain: str,
    missing_skills: List[str],
    user_level: str = "Entry level",
) -> Dict:
    """
    Generate a personalized learning roadmap based on domain and missing skills.

    The roadmap is adapted to the user's current experience level and
    filtered to emphasize missing skills.

    Parameters
    ----------
    domain        : Target job domain (e.g., "Data Science")
    missing_skills: Skills the user is missing for their target role
    user_level    : User's self-reported experience level

    Returns
    -------
    dict with stages, prioritized skills, projects, and resources
    """
    domain_roadmap = ROADMAPS.get(domain, DEFAULT_ROADMAP)
    missing_lower = [s.lower() for s in missing_skills]

    exp_order = ["Entry level", "Associate", "Mid-Senior level", "Senior", "Director", "Executive"]
    user_idx = exp_order.index(user_level) if user_level in exp_order else 0

    result = {
        "domain": domain,
        "roadmap_url": domain_roadmap["roadmap_url"],
        "user_level": user_level,
        "stages": [],
        "priority_skills": [],
        "next_steps": [],
    }

    for stage_name, stage_info in domain_roadmap["stages"].items():
        stage_skills = stage_info["skills"]

        # Highlight which skills in this stage are missing
        missing_in_stage = [s for s in stage_skills if s.lower() in missing_lower]
        have_in_stage = [s for s in stage_skills if s.lower() not in missing_lower]

        result["stages"].append({
            "name": stage_name,
            "skills": stage_skills,
            "missing_here": missing_in_stage,
            "already_have": have_in_stage,
            "projects": stage_info["projects"],
            "resources": stage_info["resources"],
        })

        result["priority_skills"].extend(missing_in_stage)

    # Determine which stage to focus on based on experience level
    if user_idx <= 1:
        focus_stage = "Beginner"
    elif user_idx <= 3:
        focus_stage = "Intermediate"
    else:
        focus_stage = "Advanced"

    result["recommended_focus_stage"] = focus_stage

    # Build next steps checklist
    priority = result["priority_skills"][:8]  # Top 8 missing skills
    if priority:
        result["next_steps"] = [
            f"Learn **{skill}** — look for resources in the roadmap stages above"
            for skill in priority[:5]
        ]
    else:
        result["next_steps"] = [
            "You have strong skill coverage! Focus on building portfolio projects.",
            "Consider contributing to open-source projects in your domain.",
        ]

    # Add roadmap.sh reference
    result["next_steps"].append(
        f"Follow the community roadmap at: {domain_roadmap['roadmap_url']}"
    )

    return result


def get_skill_prerequisites(skill: str, domain: str = "") -> List[str]:
    """
    Return common prerequisites for learning a skill.
    These are domain-knowledge-based, not data-derived — documented as such.
    """
    prerequisites = {
        "machine learning": ["Python", "Statistics", "Linear Algebra", "NumPy", "Pandas"],
        "deep learning": ["Machine Learning", "Python", "NumPy", "Linear Algebra"],
        "tensorflow": ["Python", "NumPy", "Machine Learning"],
        "pytorch": ["Python", "NumPy", "Machine Learning"],
        "kubernetes": ["Docker", "Linux", "Networking", "YAML"],
        "spark": ["Python", "SQL", "Distributed Computing basics"],
        "airflow": ["Python", "SQL", "Basic ETL concepts"],
        "kafka": ["Distributed Systems basics", "Java or Python"],
        "react": ["HTML", "CSS", "JavaScript", "Node.js basics"],
        "docker": ["Linux", "Command Line", "Networking basics"],
        "terraform": ["Cloud Computing basics", "AWS/GCP/Azure account"],
        "penetration testing": ["Networking", "Linux", "Python", "Network Security"],
    }
    return prerequisites.get(skill.lower(), [])
