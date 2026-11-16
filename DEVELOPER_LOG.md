Developer Log: James Kibira Kiruma

Role: Data Analyst & Statistician
Focus: Full-Stack Development, Statistical Modeling, Data Engineering
Date: November 2026

1. Technical Projects

Kirinyaga Stats Hub (Full-Stack Web & Android App)

· Tech Stack: Python, Streamlit, SQLite, Canva, AppsGeyser.
· Architecture: Developed a centralized portal for university students. Implemented a relational SQLite database to manage real-time notices, forum Q&A threads, and a resource vault using BLOB data types for file storage.
· Security: Built an Admin authentication system using st.session_state to restrict data deletion and moderation capabilities.
· Deployment: Deployed the web app via Streamlit Community Cloud and wrapped it into an installable Android APK.

M-PESA Spending Tracker & Web App

· Tech Stack: Python, Pandas, SQLite, Streamlit.
· Data Pipeline: Engineered a script to extract and clean 3,137 transactions from password-protected PDF statements.
· Database: Stored cleaned data in a local SQLite database and utilized SQL queries for categorization.
· Deployment: Deployed a live Streamlit interface allowing users to upload CSVs for automated visualization.

Kenya DHS 2022 Malnutrition Analysis

· Tech Stack: R, RStudio, Logistic Regression.
· Analysis: Processed 19,530 records from the KDHS. Applied complex survey weights to determine a stunting prevalence of 17.35%.
· Modeling: Built a multivariate logistic regression model to identify significant socioeconomic determinants.

Personal Portfolio Website

· Tech Stack: Python, Streamlit.
· Deployment: Live at james-kiruma.streamlit.app. Integrated project showcases, tech stack display, and a functional contact form.

2. Career & Professional Development

· Resume: Developed an ATS-friendly, 1-page technical resume highlighting data engineering and statistical modeling projects.
· LinkedIn: Optimized profile with technical headline, project media, and "Open to Work" status (Recruiters only). Published a technical post detailing the Kirinyaga Stats Hub architecture.
· Applications: Submitted application for the Lochmueller Group 2027 Data Analyst/Consultant Internship.

3. Key Technical Learnings

· Database Caching: Resolved SQLite schema update failures by versioning database files (e.g., stats_hub_v3.db) to force server refreshes.
· Data Persistence: Implemented file upload storage by converting files to binary bytes and storing them as BLOBs in SQLite.
· UI/UX: Utilized custom CSS within Streamlit to override default themes and create a modern interface.
· Session State: Managed user authentication and chat history using Streamlit's st.session_state.

4. Code Metrics

· Total Code Written: 5,603+ lines (Python, R, SQL).
· Final App Code: 231 lines (Kirinyaga Stats Hub).
· Deployments: 3 live web applications, 1 Android APK.
