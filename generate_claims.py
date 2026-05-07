import pandas as pd
import numpy as np
from faker import Faker
import random
from datetime import datetime, timedelta

fake = Faker('en_US')
random.seed(42)
np.random.seed(42)

# ── CONFIG ──────────────────────────────────────────────────────────────────
N_PATIENTS   = 300
N_PROVIDERS  = 60
N_CLAIMS     = 2000
FRAUD_RATE   = 0.15   # 15% of claims will be fraudulent

# ── REFERENCE DATA ──────────────────────────────────────────────────────────
DIAGNOSIS_CODES = {
    'G30.9':  'Alzheimer\'s disease',
    'G20':    'Parkinson\'s disease',
    'I69.354':'Hemiplegia following cerebral infarction',
    'M79.3':  'Panniculitis',
    'F03.90': 'Unspecified dementia',
    'G35':    'Multiple sclerosis',
    'I63.9':  'Cerebral infarction',
    'M54.5':  'Low back pain',
}

PROVIDER_TYPES = ['Home Health Agency', 'Skilled Nursing Facility',
                  'Adult Day Care', 'Assisted Living', 'Hospice Care']

US_STATES = ['VA', 'MD', 'NC', 'DC', 'PA', 'NY', 'FL', 'TX', 'OH', 'GA']

CARE_SERVICES = ['Personal Care', 'Skilled Nursing', 'Physical Therapy',
                 'Occupational Therapy', 'Homemaker Services', 'Respite Care']

# ── GENERATE PATIENTS ────────────────────────────────────────────────────────
patients = []
for i in range(N_PATIENTS):
    dob = fake.date_of_birth(minimum_age=65, maximum_age=95)
    # ~5% chance patient is deceased (for fraud injection later)
    is_deceased = random.random() < 0.05
    death_date  = (dob + timedelta(days=random.randint(24000, 30000))
                   if is_deceased else None)
    patients.append({
        'patient_id':   f'PAT{i+1:04d}',
        'patient_name': fake.name(),
        'dob':          dob,
        'state':        random.choice(US_STATES),
        'zip_code':     fake.zipcode(),
        'policy_number':f'GW{random.randint(100000,999999)}',
        'is_deceased':  is_deceased,
        'death_date':   death_date,
    })
patients_df = pd.DataFrame(patients)

# ── GENERATE PROVIDERS ───────────────────────────────────────────────────────
providers = []
for i in range(N_PROVIDERS):
    # ~10% are "ghost" providers registered very recently
    is_ghost    = random.random() < 0.10
    reg_date    = (fake.date_between(start_date='-3m', end_date='today')
                   if is_ghost
                   else fake.date_between(start_date='-10y', end_date='-1y'))
    providers.append({
        'provider_id':   f'PRV{i+1:04d}',
        'provider_name': fake.company() + ' Care Services',
        'provider_type': random.choice(PROVIDER_TYPES),
        'state':         random.choice(US_STATES),
        'npi_number':    f'NPI{random.randint(1000000000,9999999999)}',
        'registered_date': reg_date,
        'is_ghost_provider': is_ghost,
    })
providers_df = pd.DataFrame(providers)

# ── GENERATE BASE CLAIMS ─────────────────────────────────────────────────────
claims = []
start_date = datetime(2023, 1, 1)
end_date   = datetime(2024, 12, 31)

for i in range(N_CLAIMS):
    patient  = patients_df.sample(1).iloc[0]
    provider = providers_df.sample(1).iloc[0]
    diag_code, diag_desc = random.choice(list(DIAGNOSIS_CODES.items()))

    claim_date    = fake.date_between(start_date=start_date, end_date=end_date)
    care_hours    = round(random.uniform(2, 8), 1)
    hourly_rate   = random.uniform(25, 85)
    billed_amount = round(care_hours * hourly_rate, 2)

    claims.append({
        'claim_id':      f'CLM{i+1:05d}',
        'patient_id':    patient['patient_id'],
        'provider_id':   provider['provider_id'],
        'claim_date':    claim_date,
        'service_type':  random.choice(CARE_SERVICES),
        'diagnosis_code':diag_code,
        'diagnosis_desc':diag_desc,
        'care_hours':    care_hours,
        'hourly_rate':   round(hourly_rate, 2),
        'billed_amount': billed_amount,
        'state':         patient['state'],
        'is_fraud':      False,
        'fraud_type':    None,
    })

claims_df = pd.DataFrame(claims)
claims_df['claim_date'] = pd.to_datetime(claims_df['claim_date'])

# ── INJECT FRAUD ─────────────────────────────────────────────────────────────
# We'll inject 4 fraud types across the fraud pool
fraud_indices = random.sample(range(N_CLAIMS), int(N_CLAIMS * FRAUD_RATE))
fraud_pool    = {
    'duplicate_claim':        fraud_indices[:75],
    'deceased_patient':       fraud_indices[75:105],
    'inflated_hours':         fraud_indices[105:195],
    'phantom_round_amount':   fraud_indices[195:],
}

# Type 1 — Duplicate claims (same provider, patient, same date, same amount)
dup_source = claims_df.iloc[fraud_pool['duplicate_claim']].copy()
for idx in fraud_pool['duplicate_claim']:
    src = claims_df.loc[idx]
    claims_df.loc[idx, 'is_fraud']   = True
    claims_df.loc[idx, 'fraud_type'] = 'duplicate_claim'
    # Shift date by 0-2 days to simulate slightly delayed duplicate
    claims_df.loc[idx, 'claim_date'] = (
        src['claim_date'] + timedelta(days=random.randint(0,2))
    )

# Type 2 — Deceased patient billing (claim filed after death)
deceased_patients = patients_df[patients_df['is_deceased']]['patient_id'].tolist()
if deceased_patients:
    for idx in fraud_pool['deceased_patient']:
        pat_id = random.choice(deceased_patients)
        death  = patients_df[patients_df['patient_id']==pat_id]['death_date'].values[0]
        if death is not None:
            claims_df.loc[idx, 'patient_id']  = pat_id
            claims_df.loc[idx, 'claim_date']  = pd.Timestamp(death) + timedelta(days=random.randint(10,180))
            claims_df.loc[idx, 'is_fraud']    = True
            claims_df.loc[idx, 'fraud_type']  = 'deceased_patient_billing'

# Type 3 — Inflated hours (>16 hours/day billed per patient)
for idx in fraud_pool['inflated_hours']:
    inflated = round(random.uniform(17, 24), 1)
    claims_df.loc[idx, 'care_hours']    = inflated
    claims_df.loc[idx, 'billed_amount'] = round(inflated * claims_df.loc[idx,'hourly_rate'], 2)
    claims_df.loc[idx, 'is_fraud']      = True
    claims_df.loc[idx, 'fraud_type']    = 'inflated_hours'

# Type 4 — Phantom / round amount (suspiciously round billed amounts)
for idx in fraud_pool['phantom_round_amount']:
    round_amount = random.choice([500, 750, 1000, 1250, 1500, 2000, 2500])
    claims_df.loc[idx, 'billed_amount'] = round_amount
    claims_df.loc[idx, 'care_hours']    = round(round_amount / claims_df.loc[idx,'hourly_rate'], 1)
    claims_df.loc[idx, 'is_fraud']      = True
    claims_df.loc[idx, 'fraud_type']    = 'phantom_round_amount'

# ── SAVE FILES ───────────────────────────────────────────────────────────────
claims_df.to_csv('claims_raw.csv',     index=False)
patients_df.to_csv('patients.csv',     index=False)
providers_df.to_csv('providers.csv',   index=False)

# ── QUICK SUMMARY ────────────────────────────────────────────────────────────
print("=" * 52)
print("  DATASET GENERATED SUCCESSFULLY")
print("=" * 52)
print(f"\n  Total claims    : {len(claims_df):,}")
print(f"  Total patients  : {len(patients_df):,}")
print(f"  Total providers : {len(providers_df):,}")
print(f"\n  Fraud breakdown:")
fraud_summary = claims_df[claims_df['is_fraud']].groupby('fraud_type').size()
for ftype, count in fraud_summary.items():
    print(f"    {ftype:<30} {count} claims")
print(f"\n  Overall fraud rate : {claims_df['is_fraud'].mean()*100:.1f}%")
print(f"  Total $ billed     : ${claims_df['billed_amount'].sum():,.2f}")
print(f"  Fraud $ at risk    : ${claims_df[claims_df['is_fraud']]['billed_amount'].sum():,.2f}")
print(f"\n  Files saved:")
print(f"    claims_raw.csv")
print(f"    patients.csv")
print(f"    providers.csv")
print("=" * 52)
