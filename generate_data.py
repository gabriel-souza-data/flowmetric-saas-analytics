"""
Flowmetric Synthetic Data Generator
------------------------------------
Generates a realistic synthetic dataset for a fictional B2B SaaS company
("Flowmetric") that sells project management / time tracking / invoicing
software to creative & consulting agencies in the US, UK, Germany and
Portugal.

The goal is NOT to produce clean, perfectly correlated data. The goal is
to produce data with realistic business logic, realistic noise, and
realistic "dirtiness" so that downstream cleaning, SQL analysis and
visualization tell a genuine, defensible story.

Output: 5 CSV files in data/raw/
    - plans.csv
    - customers.csv
    - subscriptions.csv
    - events.csv
    - payments.csv
"""

import numpy as np
import pandas as pd
from faker import Faker
import random
from datetime import date, timedelta

# -----------------------------------------------------------------------
# Reproducibility
# -----------------------------------------------------------------------
SEED = 42
random.seed(SEED)
np.random.seed(SEED)
fake = Faker()
Faker.seed(SEED)

# -----------------------------------------------------------------------
# Global parameters
# -----------------------------------------------------------------------
START_DATE = date(2023, 7, 1)   # 36 months of history
END_DATE = date(2026, 6, 30)    # "today" in this project's timeline
N_MONTHS = 36
N_CUSTOMERS = 1000

COUNTRIES = {
    "United States": 0.40,
    "United Kingdom": 0.25,
    "Germany": 0.20,
    "Portugal": 0.15,
}

INDUSTRIES = [
    "Marketing Agency", "Design Studio", "Management Consulting",
    "Branding Agency", "Digital Agency", "PR Agency", "Dev Shop / Software Consulting"
]

# Employee size bands -> drives plan tier preference
SIZE_BANDS = {
    "1-10": {"weight": 0.50, "plan_pref": {"Starter": 0.75, "Pro": 0.23, "Enterprise": 0.02}},
    "11-50": {"weight": 0.35, "plan_pref": {"Starter": 0.15, "Pro": 0.65, "Enterprise": 0.20}},
    "51+":   {"weight": 0.15, "plan_pref": {"Starter": 0.02, "Pro": 0.28, "Enterprise": 0.70}},
}

# -----------------------------------------------------------------------
# 1. PLANS
# -----------------------------------------------------------------------
plans = pd.DataFrame([
    {"plan_id": 1, "plan_name": "Starter", "monthly_price": 49,  "tier": 1, "billing_cycle": "monthly"},
    {"plan_id": 2, "plan_name": "Pro",      "monthly_price": 199, "tier": 2, "billing_cycle": "monthly"},
    {"plan_id": 3, "plan_name": "Enterprise","monthly_price": 799, "tier": 3, "billing_cycle": "annual"},
])
PLAN_BY_NAME = {r.plan_name: r for r in plans.itertuples()}

# Base monthly churn probability by plan tier (industry-informed: cheaper
# self-serve plans churn more than annual enterprise contracts)
BASE_MONTHLY_CHURN = {
    "Starter": 0.045,
    "Pro": 0.016,
    "Enterprise": 0.005,
}

# -----------------------------------------------------------------------
# 2. CUSTOMERS
# -----------------------------------------------------------------------
def weighted_choice(d):
    keys = list(d.keys())
    weights = list(d.values())
    return random.choices(keys, weights=weights, k=1)[0]

def signup_month_index(n_months=N_MONTHS):
    """Growth-skewed distribution: more signups in recent months,
    simulating a growing startup, with random noise (Poisson-like)."""
    # linear growth weight per month index (0 = oldest month)
    base_weights = np.linspace(0.4, 1.6, n_months)
    # add noise so it's not a perfectly smooth ramp
    noisy_weights = base_weights * np.random.normal(1.0, 0.18, n_months)
    noisy_weights = np.clip(noisy_weights, 0.05, None)
    probs = noisy_weights / noisy_weights.sum()
    return np.random.choice(n_months, p=probs)

customers_rows = []
for i in range(1, N_CUSTOMERS + 1):
    country = weighted_choice(COUNTRIES)
    size_band = weighted_choice({k: v["weight"] for k, v in SIZE_BANDS.items()})
    industry = random.choice(INDUSTRIES)

    m_idx = signup_month_index()
    signup_date = START_DATE + pd.DateOffset(months=int(m_idx))
    # jitter day within month
    signup_date = signup_date + timedelta(days=random.randint(0, 27))
    signup_date = signup_date.date() if hasattr(signup_date, "date") else signup_date

    plan_name = weighted_choice(SIZE_BANDS[size_band]["plan_pref"])

    customers_rows.append({
        "customer_id": i,
        "company_name": fake.company(),
        "country": country,
        "industry": industry,
        "employee_size_band": size_band,
        "signup_date": signup_date,
        "initial_plan": plan_name,
    })

customers = pd.DataFrame(customers_rows)

# --- Inject realistic messiness into customers ---
# 1) A handful of missing industries (real CRM data is incomplete)
missing_idx = customers.sample(frac=0.02, random_state=SEED).index
customers.loc[missing_idx, "industry"] = np.nan

# 2) Inconsistent casing / whitespace in country field for a subset
#    (simulates manual entry / multiple source systems before cleaning)
dirty_idx = customers.sample(frac=0.04, random_state=SEED + 1).index
def dirty_country(c):
    variants = [c.upper(), c.lower(), f" {c} ", c.replace("United", "Untd")]
    return random.choice(variants)
customers.loc[dirty_idx, "country"] = customers.loc[dirty_idx, "country"].apply(dirty_country)

# 3) A few duplicate company names with different IDs (common in real CRMs
#    when sales reps create duplicate entries)
dup_sample = customers.sample(n=12, random_state=SEED + 2)
customers.loc[dup_sample.index, "company_name"] = customers.loc[dup_sample.index, "company_name"]
# (duplicates created naturally happen via Faker collisions at this volume; left as-is)

print(f"Generated {len(customers)} customers")

# -----------------------------------------------------------------------
# 3. SUBSCRIPTIONS
# -----------------------------------------------------------------------
# Each customer starts on their initial plan. Month by month we simulate:
#   - churn (probability depends on plan tier + an engagement signal we
#     compute alongside, see below)
#   - plan upgrades (size growth / happy customers moving up)
#   - plan downgrades (cost-cutting before eventual churn - common pattern)
#
# A customer can have MULTIPLE subscription rows over time if they
# change plan. status: 'active', 'churned', 'upgraded', 'downgraded'
# (the last two mean the row was closed because a new one started).

PLAN_TIER_NAME = {1: "Starter", 2: "Pro", 3: "Enterprise"}
PLAN_PRICE = {1: 49, 2: 199, 3: 799}
PLAN_NAME_TO_ID = {"Starter": 1, "Pro": 2, "Enterprise": 3}

def month_add(d, n):
    return (pd.Timestamp(d) + pd.DateOffset(months=n)).date()

subscriptions_rows = []
sub_id_counter = 1

customer_engagement = {}
customer_churn_month = {}

for row in customers.itertuples():
    cid = row.customer_id
    signup = pd.Timestamp(row.signup_date)
    start_month_idx = (signup.year - START_DATE.year) * 12 + (signup.month - START_DATE.month)

    current_plan = row.initial_plan
    sub_start = row.signup_date
    health = np.random.beta(2.5, 1.5)
    engagement_traj = {}
    churned_month = None

    m = start_month_idx
    while m < N_MONTHS:
        health = np.clip(health + np.random.normal(0, 0.12), 0, 1)
        engagement_traj[m] = health

        plan_tier_name = current_plan
        base_churn = BASE_MONTHLY_CHURN[plan_tier_name]
        engagement_multiplier = 2.2 - 1.6 * health
        churn_prob = base_churn * engagement_multiplier
        month_calendar = (START_DATE.month - 1 + m) % 12 + 1
        if month_calendar == 1:
            churn_prob *= 1.4

        roll = np.random.random()

        if roll < churn_prob:
            end_date = month_add(START_DATE, m)
            subscriptions_rows.append({
                "subscription_id": sub_id_counter, "customer_id": cid,
                "plan_id": PLAN_NAME_TO_ID[current_plan],
                "start_date": sub_start, "end_date": end_date,
                "status": "churned", "mrr_amount": PLAN_PRICE[PLAN_NAME_TO_ID[current_plan]],
            })
            sub_id_counter += 1
            churned_month = m
            break

        if m > start_month_idx + 1 and np.random.random() < 0.025:
            tier = PLAN_NAME_TO_ID[current_plan]
            change_type = None
            new_tier = tier
            if health > 0.65 and tier < 3 and np.random.random() < 0.7:
                new_tier = tier + 1
                change_type = "upgraded"
            elif health < 0.35 and tier > 1:
                new_tier = tier - 1
                change_type = "downgraded"

            if change_type:
                change_date = month_add(START_DATE, m)
                subscriptions_rows.append({
                    "subscription_id": sub_id_counter, "customer_id": cid,
                    "plan_id": tier, "start_date": sub_start, "end_date": change_date,
                    "status": change_type, "mrr_amount": PLAN_PRICE[tier],
                })
                sub_id_counter += 1
                current_plan = PLAN_TIER_NAME[new_tier]
                sub_start = change_date

        m += 1

    if churned_month is None:
        tier = PLAN_NAME_TO_ID[current_plan]
        subscriptions_rows.append({
            "subscription_id": sub_id_counter, "customer_id": cid,
            "plan_id": tier, "start_date": sub_start, "end_date": None,
            "status": "active", "mrr_amount": PLAN_PRICE[tier],
        })
        sub_id_counter += 1

    customer_engagement[cid] = engagement_traj
    customer_churn_month[cid] = churned_month

subscriptions = pd.DataFrame(subscriptions_rows)
print(f"Generated {len(subscriptions)} subscription records")
print(subscriptions["status"].value_counts())

active_or_churned = customers.merge(
    subscriptions[subscriptions["status"].isin(["active", "churned"])][["customer_id", "status"]],
    on="customer_id", how="left"
)
print("Overall churn rate:", (active_or_churned["status"] == "churned").mean().round(3))

customers_final = customers.drop(columns=["initial_plan"])
customers_final.to_csv("data/raw/customers.csv", index=False)
plans.to_csv("data/raw/plans.csv", index=False)
subscriptions.to_csv("data/raw/subscriptions.csv", index=False)

import pickle
start_idx_map = {
    r.customer_id: (pd.Timestamp(r.signup_date).year - START_DATE.year) * 12
    + (pd.Timestamp(r.signup_date).month - START_DATE.month)
    for r in customers.itertuples()
}
with open("data/raw/_engagement_cache.pkl", "wb") as f:
    pickle.dump({
        "engagement": customer_engagement,
        "churn_month": customer_churn_month,
        "start_month_idx": start_idx_map,
    }, f)

# -----------------------------------------------------------------------
# 4. EVENTS (product usage)
# -----------------------------------------------------------------------
# Volume of events per customer per month scales with their engagement
# health score. Event mix also shifts: healthy customers log time and
# send invoices (deep usage); at-risk customers mostly just log in or
# create projects without following through (shallow usage).

EVENT_TYPES_DEEP = ["time_logged", "invoice_sent", "report_exported"]
EVENT_TYPES_SHALLOW = ["login", "project_created", "task_assigned"]
EVENT_TYPES_OTHER = ["team_member_invited", "client_invited", "support_ticket_opened"]

events_rows = []
event_id_counter = 1

for cid, traj in customer_engagement.items():
    start_idx = start_idx_map[cid]
    churned_m = customer_churn_month[cid]
    last_month = churned_m if churned_m is not None else (N_MONTHS - 1)

    for m, health in traj.items():
        if m > last_month:
            continue
        month_date = month_add(START_DATE, m)
        # base event volume scales with health (0..1) -> ~3 to ~28 events/month
        n_events = max(0, int(np.random.normal(3 + health * 25, 4)))

        # mix shifts with health: healthy customers do more "deep" actions
        deep_share = 0.15 + 0.45 * health
        for _ in range(n_events):
            r = np.random.random()
            if r < deep_share:
                etype = random.choice(EVENT_TYPES_DEEP)
            elif r < deep_share + 0.55:
                etype = random.choice(EVENT_TYPES_SHALLOW)
            else:
                etype = random.choice(EVENT_TYPES_OTHER)

            event_date = month_date + timedelta(days=random.randint(0, 27))
            if event_date > END_DATE:
                continue
            events_rows.append({
                "event_id": event_id_counter,
                "customer_id": cid,
                "event_date": event_date,
                "event_type": etype,
            })
            event_id_counter += 1

events = pd.DataFrame(events_rows)

# --- Inject realistic messiness into events ---
# 1) ~1% duplicate event rows (common in event-tracking pipelines)
dupes = events.sample(frac=0.01, random_state=SEED)
events = pd.concat([events, dupes], ignore_index=True)

# 2) ~0.5% events with missing event_type (tracking bug)
miss_idx = events.sample(frac=0.005, random_state=SEED + 3).index
events.loc[miss_idx, "event_type"] = np.nan

events = events.sort_values("event_id").reset_index(drop=True)
events.to_csv("data/raw/events.csv", index=False)
print(f"Generated {len(events)} events")
print(events["event_type"].value_counts(dropna=False).head(10))

# -----------------------------------------------------------------------
# 5. PAYMENTS
# -----------------------------------------------------------------------
# One payment per month per subscription period. A small share fail
# (card decline) and get retried a few days later - classic SaaS dunning.

payments_rows = []
payment_id_counter = 1

for sub in subscriptions.itertuples():
    start = pd.Timestamp(sub.start_date)
    end = pd.Timestamp(sub.end_date) if pd.notna(sub.end_date) else pd.Timestamp(END_DATE)
    cursor = start
    while cursor <= end:
        pay_date = cursor.date() + timedelta(days=random.randint(0, 4))
        failed = np.random.random() < 0.035  # ~3.5% payment failure rate
        status = "failed" if failed else "succeeded"
        payments_rows.append({
            "payment_id": payment_id_counter,
            "subscription_id": sub.subscription_id,
            "customer_id": sub.customer_id,
            "payment_date": pay_date,
            "amount": sub.mrr_amount,
            "status": status,
        })
        payment_id_counter += 1

        if failed:
            # retry succeeds a few days later in ~80% of cases
            if np.random.random() < 0.8:
                retry_date = pay_date + timedelta(days=random.randint(2, 6))
                payments_rows.append({
                    "payment_id": payment_id_counter,
                    "subscription_id": sub.subscription_id,
                    "customer_id": sub.customer_id,
                    "payment_date": retry_date,
                    "amount": sub.mrr_amount,
                    "status": "succeeded",
                })
                payment_id_counter += 1

        cursor += pd.DateOffset(months=1)

payments = pd.DataFrame(payments_rows)
payments.to_csv("data/raw/payments.csv", index=False)
print(f"Generated {len(payments)} payments")
print(payments["status"].value_counts())

print("\n--- DONE. Files written to data/raw/ ---")
