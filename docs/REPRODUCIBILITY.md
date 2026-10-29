# Reproducibility & Evaluation Report

## 1. Reproducibility Guarantee

The synthetic data generation pipeline uses Python's standard `random.Random(seed)` with fixed seed `20261022`.

### Verification Procedure
1. Execute generation with seed `20261022` to produce dataset $D_1$.
2. Compute SHA-256 digests for each exported CSV file:
   - `customers.csv`
   - `kyc_requirements.csv`
   - `documents.csv`
   - `verifications.csv`
   - `risk_ratings.csv`
   - `review_cases.csv`
   - `beneficial_ownership.csv`
   - `alerts.csv`
   - `audit_events.csv`
   - `ground_truth.csv`
3. Execute generation again in a clean directory with the exact same seed to produce $D_2$.
4. Verify that:
   $$\text{SHA256}(D_1[table]) == \text{SHA256}(D_2[table]) \quad \forall \, table$$
5. Zero row count divergence, zero schema mismatch, zero missing foreign keys.

---

## 2. Evaluation Metrics Definitions

The evaluation engine calculates the following measurable quality and performance indicators:

1. **KYC Completeness Rate:**
   $$\frac{\sum \text{Customer Completeness \%}}{\text{Total Customers}}$$

2. **Mandatory Evidence Compliance Rate:**
   $$\frac{\text{Customers with 100\% Mandatory Evidence}}{\text{Total Customers}}$$

3. **Exception Detection Precision:**
   $$\text{Precision} = \frac{\text{True Positives (TP)}}{\text{True Positives (TP)} + \text{False Positives (FP)}}$$

4. **Exception Detection Recall:**
   $$\text{Recall} = \frac{\text{True Positives (TP)}}{\text{True Positives (TP)} + \text{False Negatives (FN)}}$$

5. **False Positive Rate (FPR):**
   $$\text{FPR} = \frac{\text{False Positives (FP)}}{\text{False Positives (FP)} + \text{True Negatives (TN)}}$$

6. **Overdue Review Rate:**
   $$\frac{\text{Overdue Unclosed Reviews}}{\text{Total Active Reviews}}$$

7. **Ownership Reconciliation Failure Rate:**
   $$\frac{\text{Businesses with Ownership} \ne 100\%}{\text{Total Businesses Evaluated}}$$

8. **Foreign-Key Violation Count:**
   Target: **0** (enforced by schema constraints and generator DAG order).

9. **Audit Event Coverage:**
   $$\frac{\text{Entities with Corresponding Audit Records}}{\text{Total Entities Subject to Audited Lifecycle Events}} = 100\%$$
