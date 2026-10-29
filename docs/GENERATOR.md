# Synthetic Data Generator & Anomaly Injection Specification

## 1. Overview
The KYC Synthetic Data Generator creates deterministic, realistic compliance datasets using a fixed master seed:
`SEED = 20261022`

Baseline Volume Specifications:
- **Total Customers:** 8,000 (configurable, e.g. 100 for dev, 8,000 for full baseline)
- **Business Customers:** 1,000 (12.5% of total)
- **Documents:** 20,000
- **Review Cases:** 3,000
- **Verifications:** ~22,000+ (supporting multiple verification attempts)
- **Beneficial Ownership Records:** ~2,500+ across the 1,000 business entities
- **Risk Ratings:** 8,000+ historical assessments
- **Alerts:** ~4,500+ expiry and review alerts
- **Audit Events:** ~40,000+ immutable event logs

---

## 2. Generation Sequence

1. **Reference Seeds:** Seed `customer_types` (INDIVIDUAL, BUSINESS) and compliance `kyc_requirements` with effective date ranges.
2. **Customers:** Create customers with deterministic business identifiers `CUS-000001` through `CUS-008000`. Assign type (87.5% INDIVIDUAL, 12.5% BUSINESS), realistic jurisdictions, and onboarding channels.
3. **Risk Ratings:** Compute initial risk scoring ($0.00-100.00$) and map to LOW ($<35$), MEDIUM ($35-70$), HIGH ($>70$).
4. **Documents:** Generate required evidence matching customer type and risk tier. Assign issuance, expiry, status, and realistic government references.
5. **Verifications:** Simulate automated OCR or manual analyst reviews with realistic timestamps and reason codes.
6. **Beneficial Ownership:** For business customers, synthesize 1-4 owners with realistic percentages summing to $100.00\%$.
7. **Completeness & Status Calculation:** Run pure business rule engine to compute completeness % and derive lifecycle statuses (`PENDING_EVIDENCE`, `PENDING_VERIFICATION`, `UNDER_REVIEW`, `APPROVED`, `REJECTED`).
8. **Periodic Reviews:** Calculate review due dates based on risk tier (Low: 24m, Medium: 12m, High: 6m).
9. **Alerts & Escalations:** Detect documents nearing expiration (30d, 15d, 7d) and overdue reviews.
10. **Audit Events:** Create immutable audit history for customer state transitions, document verifications, and approvals.
11. **Controlled Anomaly Injection:** Inject the 5 distinct compliance anomalies into specific records and record labels into `ground_truth.json` / `ground_truth.csv`.

---

## 3. Anomaly Injection Strategy

Ground truth labels are maintained completely separate from operational detection inputs. The anomaly detector must independently identify these cases by evaluating operational database fields:

1. **ANOMALY-001 (Expired Document Marked Valid):**
   - Alter 25 random documents with `expiry_date` prior to today (e.g., 2026-08-15) such that `document_status = 'VALID'`.
2. **ANOMALY-002 (Customer Approved Missing Evidence):**
   - Alter 20 customers with incomplete mandatory documents or missing verification to have `lifecycle_status = 'APPROVED'`.
3. **ANOMALY-003 (Beneficial Ownership > 100%):**
   - In 15 business customers, inject an extra owner or inflate an existing owner's percentage so that the total sums to $115\%-140\%$.
4. **ANOMALY-004 (Review Closed Without Resolution):**
   - In 20 review cases, set `review_status = 'COMPLETED'`, `closed_at = NOW()`, but set `resolution_code = NULL` and `resolution_notes = ''`.
5. **ANOMALY-005 (Duplicate Document Reference Across Unrelated Customers):**
   - Take 15 document references from existing customers and assign the identical reference to a second, completely unrelated customer.
