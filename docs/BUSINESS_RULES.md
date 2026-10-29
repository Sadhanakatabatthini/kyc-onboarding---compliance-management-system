# KYC Onboarding & Compliance Management System - Business Rules

This document specifies the operational logic, eligibility criteria, risk models, review cycles, alert escalation hierarchies, and anomaly definitions enforced across the system.

---

## 1. KYC Completeness Calculation

Completeness measures whether a customer has submitted valid evidence for all requirements mandated for their legal classification and risk tier.

### 1.1 Formula
$$\text{Completeness Percentage} = \frac{\text{Satisfied Mandatory Requirements}}{\text{Total Applicable Mandatory Requirements}} \times 100$$

Where:
- $\text{Total Applicable Mandatory Requirements}$ is the count of active requirements matching `customer_type_id` and (`applicable_risk_level = 'ALL'` OR `applicable_risk_level = customer_risk_level`) on the customer's onboarding/effective date.
- $\text{Satisfied Mandatory Requirements}$ is the count of distinct requirements where at least one document meets ALL of the following:
  1. `document_type` matches requirement `document_type`.
  2. `document_status = 'VALID'`.
  3. Current system date $\le$ `expiry_date` (or `expiry_date` is NULL).
  4. At least one associated `verification` record exists with `verification_status = 'PASSED'`.

### 1.2 Edge Cases
- If $\text{Total Applicable Mandatory Requirements} == 0$, raise a `ConfigurationException` (compliance rulebook definition missing).
- Completeness alone is NEVER sufficient for approval. Approval requires verification passed, beneficial ownership reconciliations passed (for businesses), and no unresolved critical alerts.

---

## 2. Onboarding Lifecycle State Machine

```
                   ┌───────────────────────────────┐
                   │       PENDING_EVIDENCE        │
                   └───────────────┬───────────────┘
                                   │ (All mandatory docs submitted)
                                   ▼
                   ┌───────────────────────────────┐
                   │     PENDING_VERIFICATION      │
                   └───────────────┬───────────────┘
                                   │ (Verifications completed)
                                   ▼
                   ┌───────────────────────────────┐
                   │         UNDER_REVIEW          │
                   └───────┬───────────────┬───────┘
          (Meets all rules)│               │ (Fails rules / sanctions / adverse media)
                           ▼               ▼
                   ┌───────────────┐ ┌───────────────┐
                   │   APPROVED    │ │   REJECTED    │
                   └───────┬───────┘ └───────────────┘
                           │ (Anomaly/Expiry/Audit trigger)
                           ▼
                   ┌───────────────┐
                   │   EXCEPTION   │
                   └───────────────┘
```

### Transition Guards:
1. `PENDING_EVIDENCE` $\rightarrow$ `PENDING_VERIFICATION`: At least one document submitted per mandatory requirement.
2. `PENDING_VERIFICATION` $\rightarrow$ `UNDER_REVIEW`: All submitted documents have at least one verification attempt.
3. `UNDER_REVIEW` $\rightarrow$ `APPROVED`:
   - Completeness == 100%.
   - Every mandatory document has `document_status = 'VALID'` and is unexpired.
   - For business customers: beneficial ownership is submitted, verified, and $\le 100\%$.
   - Reviewer role must be `Risk / Compliance Reviewer` or `System Administrator`.
4. `UNDER_REVIEW` $\rightarrow$ `REJECTED`: Mandatory rejection reason code and justification must be recorded in the audit event.
5. Any state $\rightarrow$ `EXCEPTION`: Triggered automatically upon detection of compliance violation or anomaly.

---

## 3. Document Validity vs Verification Separation

A critical compliance principle: **A document may have successfully passed verification in the past, yet subsequently expire.**
- `verification_status`: Reflects the outcome of the evaluation when conducted (`PASSED`, `FAILED`). Immutable historical event.
- `document_status`: Operational current state (`SUBMITTED`, `VALID`, `EXPIRED`, `INVALID`, `REJECTED`).
- If system date $>$ `expiry_date`, the system must transition `document_status` to `EXPIRED`, regardless of past `PASSED` verification!

---

## 4. Expiry Alert Escalation Windows

The background alert job runs periodically and schedules alerts based on remaining days to `expiry_date`:

| Alert Type | Threshold | Severity | Recommended Action |
|---|---|---|---|
| `DOCUMENT_EXPIRY_30D` | $\le 30$ days remaining | `LOW` | Automated reminder email dispatched to customer. |
| `DOCUMENT_EXPIRY_15D` | $\le 15$ days remaining | `MEDIUM` | Operations analyst assigned to follow up. |
| `DOCUMENT_EXPIRY_7D` | $\le 7$ days remaining | `HIGH` | Urgent portal banner; analyst outreach. |
| `DOCUMENT_EXPIRED` | $< 0$ days (Expired) | `CRITICAL` | Document marked `EXPIRED`, customer flagged with `EXCEPTION`. |

**Idempotency Rule:** A document shall not have multiple active (unresolved) alerts of the same `alert_type`.

---

## 5. Risk-Based Periodic Reviews

Compliance reviews are scheduled based on customer risk tier:
- **Low Risk:** Review due every **24 months** from previous review or onboarding date.
- **Medium Risk:** Review due every **12 months**.
- **High Risk:** Review due every **6 months** (Enhanced Due Diligence - EDD).

### Review Closure Rules:
- A review case CANNOT be transitioned to `COMPLETED` without:
  1. A valid `resolution_code` (`APPROVED_RETAIN`, `DERISK_OFFBOARD`, `EXCEPTION_GRANTED`).
  2. Non-empty `resolution_notes` explaining the decision.
  3. An authorized reviewer (`assigned_reviewer_id`).
- Attempting to close a review case without resolution details is a strict compliance violation (Anomaly #4).

---

## 6. Beneficial Ownership (UBO) Rules

For corporate/business entities:
1. Natural person owners holding $\ge 25\%$ voting rights or shares must be identified.
2. Total beneficial ownership registered across all active owners must NOT exceed $100.00\%$.
3. Total exceeding $100\%$ triggers immediate `BENEFICIAL_OWNERSHIP_OVER_100` critical exception (Anomaly #3).

---

## 7. The 5 Controlled Anomaly Scenarios

| Anomaly ID | Name | Description | Detection Logic | Expected Severity |
|---|---|---|---|---|
| `ANOMALY-001` | Expired Document Marked Valid | Document with `expiry_date < CURRENT_DATE` but `document_status = 'VALID'`. | `expiry_date < NOW() AND document_status = 'VALID'` | `CRITICAL` |
| `ANOMALY-002` | Customer Approved Missing Evidence | Customer with `lifecycle_status = 'APPROVED'` but `completeness < 100%`. | `lifecycle_status = 'APPROVED' AND (missing_mandatory_count > 0 OR completeness < 100)` | `CRITICAL` |
| `ANOMALY-003` | Ownership Percentage > 100% | Sum of active ownership shares for a business customer exceeds $100.00\%$. | `SUM(ownership_percentage) > 100.00` group by `business_customer_id` | `HIGH` |
| `ANOMALY-004` | Review Closed Without Resolution | Review case with `review_status = 'COMPLETED'` but `resolution_code IS NULL` or `resolution_notes IS NULL`. | `review_status = 'COMPLETED' AND (resolution_code IS NULL OR resolution_notes IS NULL OR TRIM(resolution_notes) = '')` | `HIGH` |
| `ANOMALY-005` | Duplicate Document Reference | Two or more different customers share the exact same `document_reference`. | `COUNT(DISTINCT customer_id) > 1` grouped by `document_reference` | `MEDIUM` |

---

## 8. Role-Based Access Control (RBAC) Matrix

| Feature / Action | Customer | Operations Analyst | Risk / Compliance Reviewer | System Admin |
|---|---|---|---|---|
| View own onboarding progress & docs | Yes | - | - | Yes |
| Submit document evidence | Yes | Yes | - | Yes |
| Create customer records | No | Yes | No | Yes |
| Perform document verification | No | Yes | Yes | Yes |
| Approve / Reject customer KYC | No | No | Yes | Yes |
| Close review cases | No | No | Yes | Yes |
| Remediate & resolve exceptions | No | No | Yes | Yes |
| Configure rules & lead times | No | No | No | Yes |
| Trigger synthetic data generation | No | No | No | Yes |
| View system metrics & exports | No | Yes | Yes | Yes |
