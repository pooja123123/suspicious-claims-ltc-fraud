-- ══════════════════════════════════════════════════════
-- LTC Insurance Fraud Detection Queries
-- Analyst: Pooja Srivastava
-- Dataset: 2,000 synthetic LTC insurance claims
-- ══════════════════════════════════════════════════════

-- RULE 1: Inflated Hours
-- Care hours > 16 in a single day is physically impossible
SELECT claim_id, provider_id, patient_id,
       care_hours, billed_amount, claim_date
FROM claims_raw
WHERE CAST(care_hours AS REAL) > 16
ORDER BY care_hours DESC;

-- RULE 2: Deceased Patient Billing
-- Claims filed after patient death date
SELECT c.claim_id, c.claim_date, p.death_date,
       c.billed_amount, c.provider_id
FROM claims_raw c
JOIN patients p ON c.patient_id = p.patient_id
WHERE p.is_deceased = 'True'
  AND c.claim_date > p.death_date;

-- RULE 3: Phantom Round Amounts
-- Billed amounts divisible by 250 are suspiciously round
SELECT claim_id, billed_amount, provider_id,
       care_hours, hourly_rate
FROM claims_raw
WHERE CAST(billed_amount AS REAL) % 250 = 0
ORDER BY billed_amount DESC;

-- RULE 4: Ghost Providers
-- Newly registered providers billing aggressively
SELECT p.provider_id, p.provider_name,
       p.registered_date,
       COUNT(c.claim_id) AS total_claims,
       ROUND(SUM(CAST(c.billed_amount AS REAL)), 2) AS total_billed
FROM providers p
JOIN claims_raw c ON p.provider_id = c.provider_id
WHERE p.is_ghost_provider = 'True'
GROUP BY p.provider_id
ORDER BY total_billed DESC;

-- SUMMARY: Total fraud by type
SELECT fraud_type,
       COUNT(claim_id) AS fraud_claims,
       ROUND(SUM(CAST(billed_amount AS REAL)), 2) AS total_at_risk
FROM claims_raw
WHERE is_fraud = 'True'
GROUP BY fraud_type
ORDER BY total_at_risk DESC;

-- SUMMARY: Total fraud headline numbers
SELECT
    COUNT(DISTINCT claim_id) AS total_fraud_claims,
    COUNT(DISTINCT patient_id) AS patients_affected,
    COUNT(DISTINCT provider_id) AS providers_involved,
    ROUND(SUM(CAST(billed_amount AS REAL)), 2) AS total_dollars_at_risk
FROM claims_raw
WHERE is_fraud = 'True';
