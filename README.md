Flowmetric — SaaS Subscription Health & Churn Analytics
Portfolio Project | Data Analytics | Python · SQL · Power BI
A complete end-to-end data analytics project simulating the role of a data analyst at Flowmetric, a fictional B2B SaaS company selling project management, time tracking, and invoicing software to creative and consulting agencies across the United States, United Kingdom, Germany, and Portugal.
________________________________________
Business Context
Flowmetric's CEO suspects that churn is eroding revenue and that some customer segments are significantly more valuable than others. As the data analyst, the mission is to investigate four core business questions:
1.	Revenue Health — Is MRR growing? What is driving the change?
2.	Churn Analysis — Who churns, when, and in which segments?
3.	Customer LTV — Which segments generate the most lifetime value?
4.	Engagement & Early Warning — Can we predict churn before it happens?
________________________________________
Dataset
The dataset is synthetic, generated with realistic B2B SaaS business logic calibrated to industry benchmarks published by ChartMogul and ProfitWell.
Table	Rows	Description
customers	1,000	Client companies — country, industry, size band
plans	3	Starter (€49/mo) · Pro (€199/mo) · Enterprise (€799/mo)
subscriptions	1,094	Subscription history including upgrades, downgrades and churn
events	200,322	Granular product usage log (login, time tracking, invoicing, etc.)
payments	11,410	Monthly billing records including failed payments and retries
Data generation script: generate_data.py — fully reproducible with SEED = 42. Churn rates calibrated to real benchmarks: Starter ~4.5%/month, Pro ~1.6%/month, Enterprise ~0.5%/month.
Intentional data quality issues were injected to simulate real-world conditions:
•	Inconsistent country name formatting (casing, whitespace, abbreviations)
•	Missing industry values (~2% of customers)
•	Duplicate event rows (~1% — simulating tracking pipeline double-firing)
•	Negative subscription durations (33 records — day-of-month jitter)
All issues are identified, documented, and corrected in the EDA notebook.
________________________________________
Project Structure
flowmetric/
├── data/
│   ├── raw/                    # Original CSV files (as generated)
│   └── clean/                  # Cleaned CSVs exported after EDA pipeline
├── images/                     # All chart exports from Python EDA
├── notebooks/
│   ├── flowmetric_eda.ipynb    # Python EDA — cleaning + 12 KPI analysis
│   └── flowmetric_sql.ipynb    # SQL analysis — same KPIs via SQLite
├── flowmetric_BI.pbix          # Power BI dashboard (4 pages)
├── generate_data.py            # Synthetic dataset generator
├── requirements.txt            # Python dependencies
├── .gitignore                  # Files excluded from version control
└── README.md                   # Project documentation________________________________________
Tools & Techniques
Python (EDA Notebook)
•	Libraries: pandas, numpy, matplotlib, seaborn, scipy
•	Data cleaning: string normalisation, duplicate removal, null handling, date correction
•	Analysis: 12 KPIs across 4 business blocks
•	Statistical validation: t-test for engagement signal (p=0.0002)
SQL (SQLite Notebook)
•	Common Table Expressions (CTEs)
•	Window Functions: SUM() OVER, RANK() OVER, LAG() OVER
•	Date arithmetic with JULIANDAY() and STRFTIME()
•	Multi-table JOINs (up to 4 tables)
•	UNION ALL for inline reference tables
•	NULLIF() for null handling in cohort analysis
Power BI (Executive Dashboard)
•	4-page interactive dashboard
•	DAX measures for KPI calculation
•	Conditional formatting on cohort retention matrix
•	Cross-page navigation with bookmark buttons
________________________________________
Key Findings
1. Revenue Health
•	MRR grew from €3,689 → €216,550 over 36 months (+5,770%)
•	Total cumulative revenue: €3.44M
•	NRR: 82% — below the 100% industry benchmark, meaning churn exceeds expansion revenue
•	Growth is acquisition-driven; if acquisition slows, the retention problem is immediately exposed
2. Churn Analysis
Plan	Churn Rate	Avg Days to Churn
Starter	52.1%	201 days
Pro	28.2%	216 days
Enterprise	10.1%	274 days
•	208 active Starter customers currently show low engagement (at-risk cohort)
•	Geographic and industry churn differences are small (31–36%) — churn is a product problem, not a market problem
3. Customer LTV
Plan	Avg LTV	% of Total Revenue
Enterprise	€10,670	68%
Pro	€2,416	25%
Starter	€618	7%
•	Enterprise LTV is 17x higher than Starter
•	All plans have healthy LTV/CAC ratios (>3x)
•	Dev Shop / Software Consulting segment has the highest LTV (€4,190)
4. Engagement & Early Warning
•	Churned customers average 11.4% fewer product events in their first 30 days (statistically significant, p=0.0002)
•	Customers who never use time tracking or invoicing in the first 90 days are 1.40x more likely to churn (48.0% vs 34.3%)
•	Month 9 is the critical retention threshold — cohorts that survive past month 9 stabilise
•	Strongest cohort: 2024Q1 (59.6% retained at 24 months)
________________________________________
Recommendations
1.	Build a 30-day onboarding flow specifically for Starter customers to accelerate time-to-value
2.	Define deep feature activation (time_logged + invoice_sent within 90 days) as a north-star onboarding metric
3.	Trigger customer success outreach when engagement score is below 14 events at day 14
4.	Shift sales investment toward Enterprise — one Enterprise customer = 17 Starter customers in LTV
5.	Investigate 2024Q2 cohort — weakest retention at 24 months (44.3% vs 59.6% for 2024Q1)
________________________________________
Setup & Reproduction
Requirements
Python 3.11+
Install dependencies:
pip install -r requirements.txt
Run order
# 1. Generate the dataset
python generate_data.py

# 2. Open and run the EDA notebook
# notebooks/flowmetric_eda.ipynb

# 3. Open and run the SQL notebook
# notebooks/flowmetric_sql.ipynb

# 4. Open the Power BI dashboard
# flowmetric_BI.pbix
# Connect to data/clean/ folder when prompted
Note: faker is required only to regenerate the dataset. If you only want to run the analysis notebooks, faker is not needed — the clean CSVs in data/clean/ are ready to use.
________________________________________
About This Project
This project was built as part of a data analytics portfolio targeting B2B remote contractor roles in the US, UK, Ireland, and Switzerland markets. The dataset is synthetic but the business logic, KPIs, and analytical methodology reflect real-world SaaS analytics practices.

**Author:** Gabriel Souza | Lisbon, Portugal
**LinkedIn:** https://www.linkedin.com/in/gabriel-souza-5bb6123a8/
**GitHub:** https://github.com/gabriel-souza-data
**Tools:** Python · SQLite · Power BI · pandas · seaborn · scipy
**AI Assistant:** Claude (Anthropic)
**Date:** July 2026
