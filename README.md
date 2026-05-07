# Suspicious Claims: LTC Insurance Fraud Analytics

> *Long-term care insurance fraud costs US insurers an estimated $30 billion annually. This project simulates an internal fraud investigation at a large LTC insurance carrier — from raw claims data to executive recommendations.*

---

## 🔍 Project Overview

This is a **full-cycle data analyst case study** built around long-term care (LTC) insurance claims fraud detection. Using a synthetic dataset of 2,000 claims modeled after real CMS Medicare billing patterns, I identified **4 distinct fraud types**, quantified **$271,340 in fraudulent billing**, and delivered a complete analyst workflow — from SQL investigation to executive deck.

This project mirrors the day-to-day work of a fraud data analyst at a company like Genworth Financial.

---

## 📊 Live Dashboard

🔗 **[View Interactive Tableau Dashboard](https://public.tableau.com/app/profile/pooja.sriavastava/viz/MonthlyFraudTrend/LTCInsuranceFraudAnalytics)**

The dashboard includes:
- 5 live KPI tiles (total claims, fraud count, $ at risk, fraud rate, providers flagged)
- Monthly fraud trend line chart
- Fraud by provider type (interactive filter)
- Top 10 riskiest providers
- Fraud by type — total $ billed
- Action filters — click any chart to filter the entire dashboard

---

## 🚨 Key Findings

| Fraud Type | Claims | $ At Risk | Detection Signal |
|---|---|---|---|
| Inflated Hours | 167 | $222,465 | Care hours > 16 in a single day |
| Phantom Round Amounts | 108 | $146,002 | Bill divisible by $250 |
| Deceased Patient Billing | 83 | $27,335 | Claim date after death date |
| Ghost Providers | 8 providers | $92,100 | Registered same day, billing aggressively |
| **TOTAL** | **300 claims** | **$271,340** | **15% fraud rate** |

### Most shocking findings
- **98.9 hours** of care billed for a single patient in a single day
- **PAT0124 died in 2005** — providers still billing in 2024 (19 years of ghost billing)
- **All 8 ghost providers registered on the exact same date** — a coordinated fraud ring
- Fraudulent claims average **$904** vs legitimate claims at **$277** — a 3.3× gap

---

## 🗂️ Project Structure

```
suspicious-claims-ltc-fraud/
│
├── data/
│   ├── claims_raw.csv          # 2,000 synthetic LTC claims
│   ├── patients.csv            # 300 patients (incl. deceased flags)
│   └── providers.csv           # 60 providers (incl. ghost flags)
│
├── sql/
│   └── fraud_queries.sql       # 12 fraud detection SQL queries
│
├── notebooks/
│   └── fraud_eda.ipynb         # EDA notebook — 6 charts + insights
│
├── excel/
│   └── claims_risk_scorer.xlsx # Risk scoring workbook (Low/Med/High)
│
├── dashboard/
│   └── tableau_public_link.md  # Live Tableau Public link
│
├── deck/
│   └── fraud_findings_deck.pdf # Executive summary (8 slides)
│
├── generate_claims.py          # Python script to generate dataset
└── README.md
```

---

## 🛠️ Tech Stack

| Tool | Purpose |
|---|---|
| **Python** (pandas, Faker, seaborn, matplotlib) | Synthetic data generation + EDA |
| **SQL** (SQLite) | Fraud detection queries — 12 rules |
| **Tableau Public** | Interactive fraud analytics dashboard |
| **Excel** (Power Query, conditional formatting) | Risk scoring workbook |
| **PowerPoint** | Executive summary deck |

---

## 📁 Dataset

The dataset was built entirely in Python using the `Faker` library, modeled after real CMS Medicare LTC billing patterns.

- **2,000 claims** across 300 patients and 60 providers
- **4 fraud types injected deliberately** with known ground truth labels
- Realistic diagnosis codes (ICD-10), care hours, hourly rates, and billed amounts
- Covers 10 US states, 5 provider types, and 6 service categories

> No real patient or provider data was used. All records are synthetic.

---

## 🔎 SQL Fraud Detection Rules

12 targeted queries written to detect fraud patterns — no ML required:

```sql
-- Rule 1: Inflated hours (>16 hrs/day is physically impossible)
SELECT claim_id, provider_id, care_hours, billed_amount
FROM claims_raw
WHERE CAST(care_hours AS REAL) > 16
ORDER BY care_hours DESC;

-- Rule 2: Deceased patient billing
SELECT c.claim_id, c.claim_date, p.death_date, c.billed_amount
FROM claims_raw c
JOIN patients p ON c.patient_id = p.patient_id
WHERE p.is_deceased = 'True'
  AND c.claim_date > p.death_date;

-- Rule 3: Phantom round amounts
SELECT claim_id, billed_amount, provider_id
FROM claims_raw
WHERE CAST(billed_amount AS REAL) % 250 = 0
ORDER BY billed_amount DESC;

-- Rule 4: Ghost providers (registered <90 days, billing heavily)
SELECT p.provider_id, p.registered_date, COUNT(c.claim_id) AS total_claims
FROM providers p
JOIN claims_raw c ON p.provider_id = c.provider_id
WHERE p.is_ghost_provider = 'True'
GROUP BY p.provider_id
ORDER BY total_claims DESC;
```

---

## 📈 EDA Highlights

6 charts built in Python (Jupyter notebook):

1. **Fraud vs legitimate claims** — count and total $ comparison
2. **Fraud by type** — which pattern causes the most financial damage
3. **Fraud rate by provider type** — Hospice Care has the highest rate
4. **Billed amount distribution** — fraudulent claims peak at round numbers ($500, $1K, $2.5K)
5. **Monthly fraud trend** — March and November are peak fraud months
6. **Top 10 riskiest providers** — Jones-White Care Services leads at $12,197

---

## 🟢 Risk Scoring Model

Built in Excel — any fraud ops analyst can use it without writing code:

| Rule | Condition | Points |
|---|---|---|
| Inflated Hours | care_hours > 16 | 40 |
| Round Amount | billed_amount % 250 = 0 | 30 |
| Deceased Patient | claim_date > death_date | 10 |
| Ghost Provider | registered < 90 days | 20 |

**Risk Tiers:**
- 🟢 0–30 → Low Risk
- 🟡 31–60 → Medium Risk
- 🔴 61–100 → High Risk

---

## 📋 Business Recommendations

1. **Block claims with care_hours > 16** — single rule prevents $222,465 in fraud
2. **Flag round-amount billing for manual review** — no legitimate bill is perfectly round
3. **Automate deceased patient cross-check** against CMS death registry before processing
4. **90-day new provider watch list** — all 8 ghost providers would have been caught early

---

## ▶️ How to Run

**Generate the dataset:**
```bash
# Install dependencies
conda install pandas numpy faker -y

# Generate synthetic claims
python generate_claims.py
```

**Run SQL queries:**
```bash
# Load into SQLite
sqlite3 fraud_claims.db
.mode csv
.import claims_raw.csv claims_raw
.import patients.csv patients
.import providers.csv providers

# Run fraud queries
.read sql/fraud_queries.sql
```

**Open EDA notebook:**
```bash
jupyter notebook notebooks/fraud_eda.ipynb
```

---

## 👩‍💻 About

**Pooja Srivastava** — Data Analyst based in Richmond, VA

- 📊 [Tableau Public](https://public.tableau.com/app/profile/pooja.sriavastava/viz/MonthlyFraudTrend/LTCInsuranceFraudAnalytics)
- 💼 [LinkedIn](https://www.linkedin.com/in/pooja-srivastava03/)
- 🐙 [GitHub](https://github.com/pooja123123)
- 📧 poojasrivastava03@gmail.com

---

*This project was built as a portfolio case study demonstrating end-to-end data analyst skills across Python, SQL, Tableau, and Excel — applied to a real-world fraud detection problem in the long-term care insurance industry.*
