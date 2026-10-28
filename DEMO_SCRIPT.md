# CareerPulse — 5 to 7 Minute Project Demonstration Script

**Project Title:** CareerPulse: AI-Powered Job Market Intelligence and Career Readiness Analyzer  
**Presenter:** Project Lead / Machine Learning Engineer & Full-Stack Developer  
**Audience:** Academic Evaluators, Examination Committee, Technical Peers  
**Estimated Duration:** 6 minutes 30 seconds

---

## Technical Setup Before Demo Starts
1. Ensure dependencies are active: `pip install -r requirements.txt`
2. Ensure pipeline artifacts exist: `python scripts/run_pipeline.py` (model bundle & figures generated)
3. Launch application: `streamlit run app.py` (runs on `http://localhost:8501`)
4. Have the report PDF (`reports/CareerPulse_Academic_Report.pdf`) ready for reference.

---

## Minute-by-Minute Demonstration Sequence

### [0:00 – 1:00] Scene 1: Introduction & Problem Context
* **Screen Display:** Application Home Page (`🏠 Home`)
* **Visual Actions:** Scroll smoothly over the top summary metrics (Postings, Companies, Domains, Temporal Window). Highlight the dataset notes and prominent disclaimers.
* **Speaker Script:**
  > "Good morning, respected evaluators. Today I am presenting **CareerPulse**, an end-to-end machine learning system and career readiness analyzer. 
  > 
  > Job seekers today face significant information asymmetry: they know their current skills, but they do not know how their qualifications map to real-world employer expectations, which technical skills are truly in demand, or what experience levels are expected for their target roles. 
  > 
  > CareerPulse solves this by turning raw, unstructured job market data into actionable intelligence. The system is built on a verified schema modeling over 15,000 LinkedIn job postings spanning 2023 to 2024. Notice upfront that we maintain strict scientific integrity: we prominently label posting counts as observable recruitment demand rather than confirmed hires, and our historical data boundaries are transparently reported."

---

### [1:00 – 2:15] Scene 2: Job Market Intelligence & Company Analytics
* **Screen Display:** Navigate to `📊 Job Market Explorer`, then `🏢 Company & Role Analytics`
* **Visual Actions:**
  1. Select Domain: `Data Science` or `Machine Learning`.
  2. Filter by Year: Toggle `2023` and `2024` to show temporal trends.
  3. Inspect Top Skills chart and Experience Level distribution.
  4. Switch to Company Analytics and display top hiring organizations.
* **Speaker Script:**
  > "Moving to the **Job Market Explorer**, users can query granular trends across specialized tech domains. As we select 'Data Science', the application dynamically computes live aggregations from our processed dataset.
  > 
  > Here we observe posting distributions across 2023 and 2024, the ranking of in-demand technical competencies—such as Python, SQL, Machine Learning, and Cloud platforms—and the breakdown of experience seniority levels. 
  > 
  > In the **Company and Role Analytics** section, we can identify which organizations exhibit the highest recruitment activity for specific titles. Because all transformations and aggregations are cached via Streamlit's `@st.cache_data`, filtering is instantaneous and fully responsive."

---

### [2:15 – 3:45] Scene 3: Candidate Profile Matcher & Scoring Transparency
* **Screen Display:** Navigate to `🎯 Profile Matcher`
* **Visual Actions:**
  1. Input Target Domain: `Data Science`.
  2. Input Target Role: `Data Scientist`.
  3. Select Candidate Level: `Entry level`.
  4. Enter Candidate Skills: `Python, SQL, Pandas, Git`.
  5. Click **Analyze My Profile**.
  6. Expand the **How this score is calculated** mathematical breakdown.
* **Speaker Script:**
  > "Now let us examine the core student-facing capability: the **Candidate Profile Matcher**. 
  > 
  > Let's simulate a graduating computer science student with skills in Python, SQL, Pandas, and Git seeking an entry-level Data Scientist position. When we analyze the profile, CareerPulse computes a transparent **Profile Match Score** of 58.6 out of 100.
  > 
  > Crucially, as highlighted in our academic disclaimer, we explicitly tell the user that this score is NOT a hiring probability. Hiring outcomes depend on non-observable interview and portfolio dynamics. Instead, it is an explainable structural alignment metric computed from a multi-criteria formula: 55% weight on skill overlap, 30% on experience compatibility, and 15% on supplementary skills.
  > 
  > The system immediately isolates the candidate's exact matching competencies, identifies missing high-demand requirements such as Scikit-learn, Machine Learning, and Tableau, and displays the most relevant job postings in our dataset."

---

### [3:45 – 4:45] Scene 4: Skill Gap Analysis & Personalized Roadmap
* **Screen Display:** Navigate to `🗺 Skill Gap & Roadmap`
* **Visual Actions:**
  1. Show how missing skills automatically populate the roadmap generator.
  2. Expand the `Beginner Stage` and `Intermediate Stage` accordions.
  3. Point out verified links to official Python, Scikit-learn documentation, and `roadmap.sh`.
* **Speaker Script:**
  > "A diagnostic score is only useful if it offers an actionable path forward. The **Skill Gap and Roadmap** engine bridges this gap.
  > 
  > Rather than presenting a generic syllabus, CareerPulse generates a personalized, multi-stage roadmap tailored specifically to the candidate's missing skills and experience tier. 
  > 
  > The interface organizes required competencies into Beginner, Intermediate, and Advanced stages, pairs each stage with concrete portfolio project suggestions, and provides verified outbound links to official technology documentation and recognized open-source roadmaps like roadmap.sh."

---

### [4:45 – 5:45] Scene 5: Machine Learning Models & Experimental Rigor
* **Screen Display:** Navigate to `🤖 Model Performance`
* **Visual Actions:**
  1. Display the validation comparison table across all 5 models (Dummy, Logistic Regression, Linear SVC, Random Forest, LightGBM).
  2. Review the bar chart comparing Accuracy, Macro F1, and Weighted F1.
  3. Show the final held-out Test Set metrics and normalized Confusion Matrix.
  4. Perform a real-time live inference prediction using the text input box.
* **Speaker Script:**
  > "Behind the user interface lies our rigorous predictive machine learning pipeline. We formulated a 6-class supervised classification task: predicting the seniority tier of a job posting directly from its title and description text.
  > 
  > To ensure scientific validity:
  > First, we enforced a strict **chronological split** (70% Train, 15% Validation, 15% Test) to prevent future vocabulary from leaking into historical training.
  > Second, we deduplicated data prior to splitting and fitted all TF-IDF vectorizers exclusively on training samples.
  > 
  > We benchmarked five distinct algorithms: a Zero-R Dummy baseline, Logistic Regression, Linear SVC, Random Forest, and LightGBM. We selected our champion model based on **Macro F1-score**, which treats all seniority tiers equally despite class imbalance. 
  > 
  > Finally, we evaluated the champion model on the untouched test set, recording genuine, uninflated metrics. As shown in the confusion matrix, errors occur predominantly between adjacent seniority tiers rather than distant extremes. We can also perform live inference on any novel job description right here."

---

### [5:45 – 6:30] Scene 6: Architecture, Testing, & Conclusion
* **Screen Display:** Navigate to `📚 Data Sources & Methodology`, then show terminal with passed pytest suite.
* **Visual Actions:**
  1. Briefly show the methodology and limitations page.
  2. Show clean test execution: `pytest -v`.
  3. Display the 10-page academic report cover page.
* **Speaker Script:**
  > "To ensure enterprise-grade code quality, the repository is modularized into dedicated preprocessing, modeling, analytics, and interface layers. We maintain a suite of unit and integration tests covering cleaning, profile scoring, and edge cases with 100% pass rates.
  > 
  > Our complete deliverables include the clean GitHub repository structure, the interactive Streamlit deployment, comprehensive viva defense documentation, and the full 10-page formal academic report adhering strictly to academic formatting guidelines.
  > 
  > Thank you for your time and attention. I am now pleased to welcome any questions regarding the methodology or findings."
