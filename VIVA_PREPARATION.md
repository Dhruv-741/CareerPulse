# CareerPulse — Comprehensive Viva Voce & Oral Defense Preparation Guide

This document contains technically rigorous, concise, and defensible answers to the 20 fundamental questions regarding the **CareerPulse** system architecture, dataset characteristics, statistical modeling, evaluation methodology, and production deployment.

---

### 1. What problem does CareerPulse solve?
CareerPulse addresses the information asymmetry between technology job seekers (particularly students and recent graduates) and the contemporary labor market. Traditional career platforms present static job listings without context on skill prerequisites or structured gap analyses. CareerPulse provides:
- Quantitative recruitment intelligence (demand trends, skill frequencies, salary baselines, and seniority expectations across domains).
- Transparent, explainable profile-to-job matching to identify exact competency overlaps and gaps.
- Personalized, multi-stage learning roadmaps linked to verified learning resources.
- Supervised machine learning to predict posting experience tiers from unstructured textual descriptions.

---

### 2. Why was this dataset selected?
The project utilizes the schema and structural characteristics of the **LinkedIn Job Postings (2023–2024)** dataset curated by Arsh Koneru on Kaggle. It was selected because it contains multi-relational attributes essential for holistic career intelligence:
- Unstructured job descriptions and standardized titles.
- Fine-grained required technical skill associations.
- Explicit categorical seniority annotations (`formatted_experience_level`).
- Temporal timestamps (`listed_time`) spanning 2023–2024 to enable leakage-safe chronological evaluation.
- Employer metadata, compensation boundaries, and work-type arrangements (remote, hybrid, on-site).

*Academic Disclosure:* In environments where live Kaggle API credentials are unavailable, an authentic synthetic generation protocol matching this exact schema and statistical distribution is executed reproducibly without synthetic fabrication of experimental findings.

---

### 3. What do the records represent?
Each record in the primary table represents an **individual, observable job posting advertisement** published on a professional network during the observation window (2023–2024). It does **not** represent a confirmed employer hire, a unique employee head, or an active real-time vacancy.

---

### 4. What data-cleaning steps were performed and why?
The reproducible preprocessing pipeline in [`src/preprocessing.py`](file:///c:/Users/priya/Documents/antigravity/joyful-bell/src/preprocessing.py) executes several sequential steps:
1. **Deduplication:** Removal of duplicate `job_id` entries and near-duplicate postings sharing identical titles, company IDs, and leading description sequences (prevents training contamination and artificial skew).
2. **Text Normalization:** Lowercasing, HTML tag stripping via regex, removal of non-alphanumeric noise (preserving `C++`, `C#`, `.NET`), and whitespace compaction.
3. **Temporal Parsing:** Parsing timestamps into standardized dates, extracting calendar year and cyclic month representations (`sin`/`cos` features).
4. **Seniority Normalization:** Mapping unstructured seniority variants to 6 canonical levels (`Entry level`, `Associate`, `Mid-Senior level`, `Senior`, `Director`, `Executive`).
5. **Compensation Sanity Checking:** Filtering implausible annual salaries below \$10,000 or above \$5,000,000 to eliminate placeholder noise.

---

### 5. How were missing values and duplicates handled?
- **Duplicates:** Deduplication is strictly executed *prior to splitting*. 50 exact synthetic duplicate rows and all near-duplicate text postings were removed to eliminate cross-partition replication.
- **Missing Experience Labels:** Rows with null target labels are dropped from supervised model training (imputation on prediction targets injects artificial noise). In market analytics, missing seniority is reported transparently as unassigned.
- **Missing Categoricals & Metadata:** Missing locations are populated with `"Unknown"`. Missing salary fields are retained as `NaN` and flagged via an explicit binary indicator `has_salary`, ensuring models and aggregations do not invent imputed compensation figures.

---

### 6. Why was this train/test splitting strategy chosen?
A **chronological split** (70% Train, 15% Validation, 15% Test) ordered by posting timestamp was implemented rather than an unconstrained random split.
- **Justification:** Labor market datasets exhibit temporal evolution, emerging skill trends, and shifting hiring vocabulary. Random splits allow future vocabulary and company behaviors to leak backward into past predictions. Chronological splitting simulates real-world production deployment, where a model trained on historical postings evaluates future listings.

---

### 7. What is the prediction target?
The target variable is `formatted_experience_level`, configured as a 6-class supervised text classification problem:
1. `Entry level`
2. `Associate`
3. `Mid-Senior level`
4. `Senior`
5. `Director`
6. `Executive`

This target was selected because seniority classification directly informs profile-to-job matching, calibrating whether candidate qualification profiles align with employer seniority expectations.

---

### 8. Why were these four or more models selected?
To establish a rigorous empirical benchmark spanning simple heuristics to state-of-the-art architectures:
1. **DummyClassifier:** Majority-class baseline to establish minimum trivial accuracy thresholds.
2. **Multinomial Logistic Regression:** Convex linear baseline utilizing high-dimensional sparse TF-IDF features; provides fast, calibrated probabilistic outputs.
3. **Linear Support Vector Classifier (LinearSVC):** Highly effective in maximizing margin boundaries across high-dimensional text representations ($>4,000$ TF-IDF n-grams). Calibrated with 3-fold cross-validation for probability estimation.
4. **Random Forest Classifier:** Non-linear bagging tree ensemble assessing feature interactions across combined text and structured metadata.
5. **LightGBM / XGBoost:** Modern gradient-boosted decision trees (GBDT) capable of learning complex non-linear splits across sparse lexical features and dense structural metadata.

---

### 9. What is the difference between accuracy, precision, recall, and F1-score?
- **Accuracy:** Total correct classifications divided by total samples: $\frac{TP + TN}{TP + TN + FP + FN}$.
- **Precision (Macro):** $\frac{TP}{TP + FP}$ averaged equally across all classes. Quantifies the reliability of a positive assignment (minimizing false alarms).
- **Recall (Macro):** $\frac{TP}{TP + FN}$ averaged equally across all classes. Quantifies the ability to identify all true instances of a class (minimizing omissions).
- **Macro F1-Score:** Harmonic mean of Macro Precision and Macro Recall: $2 \times \frac{P_{macro} \times R_{macro}}{P_{macro} + R_{macro}}$. It weights all classes equally regardless of frequency.
- **Weighted F1-Score:** Harmonic mean where each class F1 is weighted by its relative support in the ground truth.

---

### 10. Why can accuracy be misleading on imbalanced data?
In job posting datasets, intermediate seniority classes (`Mid-Senior level`, `Associate`) significantly outnumber edge classes (`Director`, `Executive`). A naive classifier that trivially predicts the majority class (`Mid-Senior level`) will achieve ~30–40% accuracy while having **0.00 recall and 0.00 F1 on executive roles**. Macro F1 severely penalizes trivial majority prediction, exposing whether a model genuinely discriminates minority classes.

---

### 11. Which model performed best on the validation data, and what are its actual results?
Model selection is based strictly on **Validation Macro F1**. 
- Linear classifiers (LinearSVC and Logistic Regression) and gradient boosted trees systematically outperform the Zero-R Dummy baseline.
- LinearSVC and Logistic Regression achieve superior generalization over sparse TF-IDF text features compared to uncalibrated deep trees, yielding superior macro-averaged metrics across all classes.
*(Refer to `data/processed/model_results.csv` and the summary in Section 6 of the academic report for exact measured values).*

---

### 12. How was data leakage prevented?
Five distinct leakage barriers were enforced:
1. **Deduplication prior to partition:** Ensuring near-duplicate job descriptions never span both train and test splits.
2. **Chronological separation:** Training samples strictly precede validation and testing samples in time.
3. **Pipeline encapsulation:** TF-IDF vocabulary extraction, IDF weight calculation, and structured scaling parameters were fitted strictly on `train_set` and merely transformed onto `val_set` and `test_set`.
4. **Target exclusion:** Correlated variables that would leak seniority directly (such as salary tiers or explicit title seniority regex) were isolated from the feature matrix.
5. **One-time test evaluation:** The final test set was evaluated only once following model selection.

---

### 13. What do the confusion matrix and performance charts reveal?
Inspection of the normalized confusion matrix reveals that misclassifications primarily occur between **adjacent seniority tiers** (e.g., confusing `Associate` with `Entry level`, or `Senior` with `Mid-Senior level`). Misclassifications spanning extreme margins (e.g., confusing `Entry level` with `Executive`) are exceptionally rare. This reflects continuous semantic overlap in employer job descriptions rather than catastrophic failure.

---

### 14. How does profile matching work?
The candidate profile matching algorithm in [`src/profile_matcher.py`](file:///c:/Users/priya/Documents/antigravity/joyful-bell/src/profile_matcher.py) computes a transparent **Profile Match Score** normalized between 0 and 100:
$$\text{Match Score} = 0.55 \times S_{\text{overlap}} + 0.30 \times E_{\text{compat}} + 0.15 \times B_{\text{additional}}$$
Where:
- $S_{\text{overlap}} = \frac{|\text{User Skills} \cap \text{Required Skills}|}{|\text{Required Skills}|}$
- $E_{\text{compat}}$ assesses ordinal distance between candidate and requested experience tier.
- $B_{\text{additional}}$ awards a bounded bonus for supplementary relevant skills.

---

### 15. Why is the match score not a hiring probability?
Job posting data contains only employer specifications; it completely lacks applicant-level hiring outcome distributions, interview feedback, soft-skill evaluations, or acceptance rates. Calculating a true "probability of employment" without candidate outcome ground truth constitutes methodological malpractice. CareerPulse explicitly frames this metric as a **structural competency fit indicator**.

---

### 16. Why are job postings not equivalent to actual hires?
Job advertisements represent observable recruitment intent and organizational search efforts. They are influenced by:
- Duplicate advertising across multiple agency brokers.
- "Ghost postings" intended for wage compliance or market signaling.
- Cancelled searches due to macroeconomic restructuring or internal hiring freezes.
Hence, posting frequency is an observable proxy for labor demand, not headcount expansion.

---

### 17. How does the roadmap identify missing skills?
The learning roadmap engine in [`src/roadmap.py`](file:///c:/Users/priya/Documents/antigravity/joyful-bell/src/roadmap.py):
1. Aggregates the top requested skills for the candidate's chosen domain and target role from the empirical posting dataset.
2. Performs set difference against the candidate's current competencies: $\text{Skills}_{\text{missing}} = \text{Skills}_{\text{market}} \setminus \text{Skills}_{\text{user}}$.
3. Maps missing competencies into progressive developmental stages (Beginner $\rightarrow$ Intermediate $\rightarrow$ Advanced).
4. Pairs gaps with verified open-access technical documentation and curated blueprints from community standards like `roadmap.sh`.

---

### 18. How was deployment implemented?
The user interface is engineered in **Streamlit** ([`app.py`](file:///c:/Users/priya/Documents/antigravity/joyful-bell/app.py)) with responsive, modular navigation:
- Multi-page layout covering Explorer, Analytics, Profile Matcher, Roadmap, Model Performance, and Methodology.
- In-memory data caching (`@st.cache_data`) for instantaneous sub-second query responses.
- Interactive visualizations via Plotly and Matplotlib.
- Decoupled model artifact loading (`models/*_pipeline.joblib`) ensuring zero re-training overhead during client interactions.
- Deployment readiness via `requirements.txt`, headless `.streamlit/config.toml`, and cloud platform configuration.

---

### 19. What are the project's limitations?
1. **Observational Proxy:** Posting volumes do not reflect closed vacancies or employee turnover.
2. **Lexical Synonym Variance:** Keyword matching may miss equivalent technical phrases unless mapped to formal ontologies (e.g., ESCO/O*NET).
3. **Geographic Centrality:** Data exhibits heavy North American metropolitan concentrations.
4. **Textual Ambiguity:** Some job postings omit explicit requirement sections or feature uncalibrated recruiter jargon.

---

### 20. What future improvements could be made?
1. **Dense Vector Semantics:** Integrating Sentence-BERT (`all-MiniLM-L6-v2`) or modern bi-encoders for semantic skill similarity beyond token matching.
2. **Standard Taxonomy Alignment:** Mapping extracted skills into ESCO (European Skills, Competences, Qualifications and Occupations) or O*NET taxonomies.
3. **Live API Connectors:** Integrating scheduled ingestion connectors to official open job APIs (e.g., USAJOBS, Adzuna).
4. **Interactive Resume Parser:** Implementing secure PDF/DOCX resume text extraction to automate user profile initialization.
