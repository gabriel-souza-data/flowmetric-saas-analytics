# Flowmetric — SaaS Subscription Health & Churn Analytics

> **Portfolio Project | Data Analytics | Python · SQL · Power BI**

---

## About This Project

This project simulates the work of a data analyst embedded at **Flowmetric**, a fictional B2B SaaS company selling project management, time tracking, and invoicing software to creative and consulting agencies across the **United States, United Kingdom, Germany, and Portugal**.

The goal was to build a complete end-to-end analytics case study — from raw data generation to executive dashboard — covering the four business questions any SaaS company needs to answer:

1. **Revenue Health** — Is MRR growing? What is driving the change?
2. **Churn Analysis** — Who churns, when, and in which segments?
3. **Customer LTV** — Which segments generate the most lifetime value?
4. **Engagement & Early Warning** — Can we predict churn before it happens?

The analysis is structured in three layers:
- **Python notebooks** — data generation, cleaning, statistical analysis, and 12 KPI calculations
- **SQL (SQLite)** — same KPIs replicated using advanced SQL techniques
- **Power BI dashboard** — 4-page interactive executive dashboard

AI assistance (Claude by Anthropic) was used throughout this project as a development partner — for code generation, debugging, and methodology review. All analytical decisions, business interpretations, KPI definitions, and conclusions are the author's own.

---

## Dataset

The dataset is **synthetic**, generated from scratch using Python with realistic B2B SaaS business logic calibrated to industry benchmarks published by ChartMogul and ProfitWell.

| Table | Rows | Description |
|---|---|---|
| `customers` | 1,000 | Client companies — country, industry, employee size band |
| `plans` | 3 | Starter (€49/mo) · Pro (€199/mo) · Enterprise (€799/mo) |
| `subscriptions` | 1,094 | Subscription history including upgrades, downgrades and churn |
| `events` | 200,322 | Granular product usage log (login, time tracking, invoicing, etc.) |
| `payments` | 11,410 | Monthly billing records including failed payments and retries |

**Data generation script:** `generate_data.py` — fully reproducible with `SEED = 42`.

Churn rates calibrated to real SaaS benchmarks:
- Starter: ~4.5%/month
- Pro: ~1.6%/month
- Enterprise: ~0.5%/month

**Intentional data quality issues** were injected to simulate real-world conditions:
- Inconsistent country name formatting (casing, whitespace, abbreviations)
- Missing industry values (~2% of customers)
- Duplicate event rows (~1% — simulating tracking pipeline double-firing)
- Negative subscription durations (33 records — day-of-month jitter)

All issues are identified, documented, and corrected in the EDA notebook before any analysis is performed.

---

## Project Structure

```
flowmetric/
├── data/
│   ├── raw/                    # Original CSV files (as generated)
│   └── clean/                  # Cleaned CSVs exported after EDA pipeline
├── images/                     # All chart exports from Python EDA
├── notebooks/
│   ├── flowmetric_eda.ipynb    # Python EDA — cleaning + 12 KPI analysis
│   └── flowmetric_sql.ipynb    # SQL analysis — same KPIs via SQLite
├── powerbi/
│   └── flowmetric_BI.pbix      # Power BI dashboard (4 pages)
├── generate_data.py            # Synthetic dataset generator
├── requirements.txt            # Python dependencies
├── .gitignore                  # Files excluded from version control
└── README.md                   # Project documentation
```

---

## Tools & Techniques

### Python (EDA Notebook)
- **Libraries:** pandas, numpy, matplotlib, seaborn, scipy
- **Data cleaning:** string normalisation, duplicate removal, null handling, date correction
- **Analysis:** 12 KPIs across 4 business blocks
- **Statistical validation:** t-test for engagement signal (p=0.0002)

### SQL (SQLite Notebook)
- Common Table Expressions (CTEs)
- Window Functions: `SUM() OVER`, `RANK() OVER`, `LAG() OVER`
- Date arithmetic with `JULIANDAY()` and `STRFTIME()`
- Multi-table JOINs (up to 4 tables)
- `UNION ALL` for inline reference tables
- `NULLIF()` for null handling in cohort analysis

### Power BI (Executive Dashboard)
- 4-page interactive dashboard
- DAX measures for KPI calculation
- Conditional formatting on cohort retention matrix
- Cross-page navigation with bookmark buttons

---

## Key Findings

### 1. Revenue Health
- MRR grew from **€3,689 → €216,550** over 36 months (+5,770%)
- Total cumulative revenue: **€3.44M**
- **NRR: 82%** — below the 100% industry benchmark, meaning churn exceeds expansion revenue
- Growth is acquisition-driven; if acquisition slows, the retention problem is immediately exposed

### 2. Churn Analysis

| Plan | Churn Rate | Avg Days to Churn |
|---|---|---|
| Starter | 52.1% | 201 days |
| Pro | 28.2% | 216 days |
| Enterprise | 10.1% | 274 days |

- **208 active Starter customers** currently show low engagement (at-risk cohort)
- Geographic and industry churn differences are small (31–36%) — churn is a product problem, not a market problem

### 3. Customer LTV

| Plan | Avg LTV | % of Total Revenue |
|---|---|---|
| Enterprise | €10,670 | 68% |
| Pro | €2,416 | 25% |
| Starter | €618 | 7% |

- Enterprise LTV is **17x higher** than Starter
- All plans have healthy LTV/CAC ratios (>3x)
- Dev Shop / Software Consulting segment has the highest LTV (€4,190)

### 4. Engagement & Early Warning
- Churned customers average **11.4% fewer product events** in their first 30 days (statistically significant, p=0.0002)
- Customers who **never use time tracking or invoicing** in the first 90 days are **1.40x more likely to churn** (48.0% vs 34.3%)
- **Month 9** is the critical retention threshold — cohorts that survive past month 9 stabilise
- Strongest cohort: 2024Q1 (59.6% retained at 24 months)

---

## Recommendations

1. **Build a 30-day onboarding flow** specifically for Starter customers to accelerate time-to-value
2. **Define deep feature activation** (time_logged + invoice_sent within 90 days) as a north-star onboarding metric
3. **Trigger customer success outreach** when engagement score is below 14 events at day 14
4. **Shift sales investment toward Enterprise** — one Enterprise customer = 17 Starter customers in LTV
5. **Investigate 2024Q2 cohort** — weakest retention at 24 months (44.3% vs 59.6% for 2024Q1)

---

## How to Run

```bash
git clone https://github.com/gabriel-souza-data/flowmetric-saas-analytics.git
cd flowmetric-saas-analytics
pip install -r requirements.txt
```

Run in order:

```bash
# 1. Generate the dataset
python generate_data.py

# 2. Open and run the EDA notebook
# notebooks/flowmetric_eda.ipynb

# 3. Open and run the SQL notebook
# notebooks/flowmetric_sql.ipynb

# 4. Open the Power BI dashboard
# powerbi/flowmetric_BI.pbix
# Connect to data/clean/ folder when prompted
```

> **Note:** `faker` is required only to regenerate the dataset. If you only want to run the analysis notebooks, faker is not needed — the clean CSVs in `data/clean/` are ready to use.

---

## Author

**Gabriel Souza** — Data analyst Lisbon, Portugal · 2026
LinkedIn: https://www.linkedin.com/in/gabriel-souza-5bb6123a8/ GitHub: https://github.com/gabriel-souza-data
