# KYC Onboarding & Compliance Management System - Data Dictionary

This document provides the definitive schema specification for the KYC Onboarding & Compliance Management System, engineered for MySQL 8.0 InnoDB with foreign key constraints, indexes, and full historical traceability.

---

## 1. Table: `customer_types`
Defines legal classifications of onboarding entities.

| Column Name | Data Type | Nullable | Key / Constraint | Description |
|---|---|---|---|---|
| `customer_type_id` | INT AUTO_INCREMENT | No | PRIMARY KEY | Unique integer identifier |
| `code` | VARCHAR(32) | No | UNIQUE INDEX | Standard classification code (`INDIVIDUAL`, `BUSINESS`) |
| `name` | VARCHAR(100) | No | - | Human-readable name (e.g., "Individual Account", "Corporate Entity") |
| `description` | TEXT | Yes | - | Detailed description of the classification |
| `active_status` | BOOLEAN | No | DEFAULT TRUE | Active flag for requirement lookup |

---

## 2. Table: `customers`
Core entity for onboarded customers and applicants.

| Column Name | Data Type | Nullable | Key / Constraint | Description |
|---|---|---|---|---|
| `customer_id` | VARCHAR(32) | No | PRIMARY KEY | Deterministic business ID (e.g., `CUS-000001`) |
| `customer_type_id` | INT | No | FOREIGN KEY -> `customer_types(customer_type_id)` | Classification of the customer |
| `legal_name` | VARCHAR(255) | No | INDEX | Official legal name or registered corporate title |
| `country_code` | CHAR(2) | No | INDEX | ISO 3166-1 alpha-2 country of incorporation/residence |
| `onboarding_date` | DATE | No | INDEX | Date when onboarding was initiated |
| `lifecycle_status` | VARCHAR(32) | No | INDEX | `PENDING_EVIDENCE`, `PENDING_VERIFICATION`, `UNDER_REVIEW`, `APPROVED`, `REJECTED`, `EXCEPTION` |
| `onboarding_channel` | VARCHAR(64) | No | - | Acquisition channel (`DIGITAL_PORTAL`, `BRANCH`, `RELATIONSHIP_MANAGER`) |
| `created_at` | DATETIME | No | DEFAULT CURRENT_TIMESTAMP | Audit timestamp |
| `updated_at` | DATETIME | No | DEFAULT CURRENT_TIMESTAMP ON UPDATE | Last modification timestamp |

---

## 3. Table: `kyc_requirements`
Configurable compliance rule catalog determining required evidence by customer type and risk level.

| Column Name | Data Type | Nullable | Key / Constraint | Description |
|---|---|---|---|---|
| `requirement_id` | VARCHAR(32) | No | PRIMARY KEY | Identifier (e.g., `KYC-2026-000001`) |
| `requirement_code` | VARCHAR(64) | No | INDEX | Canonical code (`PASSPORT`, `NATIONAL_ID`, `PROOF_OF_ADDRESS`, `CERT_INCORPORATION`, `ARTICLES_OF_ASSOC`, `BENEFICIAL_OWNERSHIP_DECLARATION`, `FINANCIAL_STATEMENT`) |
| `customer_type_id` | INT | No | FOREIGN KEY -> `customer_types(customer_type_id)` | Applicable customer category |
| `applicable_risk_level` | VARCHAR(16) | No | INDEX | `ALL`, `LOW`, `MEDIUM`, `HIGH` |
| `document_type` | VARCHAR(64) | No | - | Required document classification |
| `mandatory_flag` | BOOLEAN | No | DEFAULT TRUE | If true, required for customer approval |
| `effective_from` | DATE | No | INDEX | Historical validity starting date |
| `effective_to` | DATE | Yes | INDEX | Historical validity ending date (NULL = current) |
| `active_status` | BOOLEAN | No | DEFAULT TRUE | Operational active toggle |

---

## 4. Table: `documents`
Evidence records submitted by or on behalf of customers.

| Column Name | Data Type | Nullable | Key / Constraint | Description |
|---|---|---|---|---|
| `document_id` | VARCHAR(32) | No | PRIMARY KEY | Identifier (e.g., `DOC-CUS-000001-001`) |
| `customer_id` | VARCHAR(32) | No | FOREIGN KEY -> `customers(customer_id)` | Associated customer |
| `requirement_id` | VARCHAR(32) | Yes | FOREIGN KEY -> `kyc_requirements(requirement_id)` | Requirement satisfied by this document |
| `document_type` | VARCHAR(64) | No | INDEX | Classification matching requirement |
| `issue_date` | DATE | No | - | Official date of document issuance |
| `expiry_date` | DATE | Yes | INDEX | Official document expiration date (NULL if non-expiring) |
| `submission_date` | DATE | No | - | Date document was uploaded/received |
| `document_status` | VARCHAR(32) | No | INDEX | `SUBMITTED`, `VALID`, `EXPIRED`, `INVALID`, `REJECTED` |
| `document_reference` | VARCHAR(128) | No | INDEX | Government ID/Tax ID/Doc number (must be unique per entity) |
| `created_at` | DATETIME | No | DEFAULT CURRENT_TIMESTAMP | Audit timestamp |

---

## 5. Table: `verifications`
Audit trail of manual and automated review attempts for submitted documents.

| Column Name | Data Type | Nullable | Key / Constraint | Description |
|---|---|---|---|---|
| `verification_id` | VARCHAR(32) | No | PRIMARY KEY | Identifier (e.g., `VER-DOC-000001-1`) |
| `document_id` | VARCHAR(32) | No | FOREIGN KEY -> `documents(document_id)` | Evaluated document |
| `verification_status` | VARCHAR(32) | No | INDEX | `PASSED`, `FAILED`, `PENDING_MORE_INFO` |
| `verification_method` | VARCHAR(64) | No | - | `AUTOMATED_OCR`, `MANUAL_ANALYST`, `THIRD_PARTY_BUREAU` |
| `verification_timestamp` | DATETIME | No | INDEX | Timestamp when evaluation completed |
| `reviewer_id` | VARCHAR(64) | No | - | Actor identifier (e.g., `analyst_04`, `system_ocr`) |
| `reason_code` | VARCHAR(64) | Yes | - | Reason code (e.g., `CLEAR_IMAGE`, `EXPIRED_DOC`, `TAMPER_DETECTED`) |
| `comments` | TEXT | Yes | - | Detailed analyst notes |
| `previous_status` | VARCHAR(32) | Yes | - | Document status prior to verification |
| `created_at` | DATETIME | No | DEFAULT CURRENT_TIMESTAMP | Audit timestamp |

---

## 6. Table: `risk_ratings`
Historical risk scores and levels assessed for customers.

| Column Name | Data Type | Nullable | Key / Constraint | Description |
|---|---|---|---|---|
| `risk_rating_id` | VARCHAR(32) | No | PRIMARY KEY | Identifier (e.g., `RSK-CUS-000001-01`) |
| `customer_id` | VARCHAR(32) | No | FOREIGN KEY -> `customers(customer_id)` | Customer entity |
| `risk_level` | VARCHAR(16) | No | INDEX | `LOW`, `MEDIUM`, `HIGH` |
| `risk_score` | DECIMAL(5,2) | No | - | Quantitative rating score (0.00 to 100.00) |
| `reason_codes` | JSON / TEXT | No | - | Structured reasons (e.g., `["PEP_CHECK_CLEAR", "CROSS_BORDER_HIGH"]`) |
| `assessment_date` | DATE | No | INDEX | Date risk evaluation occurred |
| `effective_from` | DATE | No | - | Beginning of validity window |
| `effective_to` | DATE | Yes | - | End of validity window (NULL = active) |
| `assessed_by` | VARCHAR(64) | No | - | Actor or rule engine (`SYSTEM_ALGO`, `compliance_officer_1`) |

---

## 7. Table: `review_cases`
Periodic and event-triggered compliance reviews.

| Column Name | Data Type | Nullable | Key / Constraint | Description |
|---|---|---|---|---|
| `review_id` | VARCHAR(32) | No | PRIMARY KEY | Identifier (e.g., `REV-CUS-000001-2026`) |
| `customer_id` | VARCHAR(32) | No | FOREIGN KEY -> `customers(customer_id)` | Associated customer |
| `review_type` | VARCHAR(32) | No | INDEX | `PERIODIC_LOW`, `PERIODIC_MEDIUM`, `PERIODIC_HIGH`, `TRIGGERED_EXCEPTION` |
| `opened_at` | DATETIME | No | INDEX | When case was initiated |
| `due_date` | DATE | No | INDEX | Regulatory deadline |
| `review_status` | VARCHAR(32) | No | INDEX | `OPEN`, `IN_PROGRESS`, `PENDING_CUSTOMER`, `COMPLETED`, `OVERDUE`, `ESCALATED` |
| `assigned_reviewer_id` | VARCHAR(64) | Yes | - | Assigned reviewer |
| `resolution_code` | VARCHAR(64) | Yes | - | Code upon closure (`APPROVED_RETAIN`, `DERISK_OFFBOARD`, `EXCEPTION_GRANTED`) |
| `resolution_notes` | TEXT | Yes | - | Mandatory justification for closure |
| `closed_at` | DATETIME | Yes | INDEX | Case closure timestamp |
| `created_at` | DATETIME | No | DEFAULT CURRENT_TIMESTAMP | Audit timestamp |

---

## 8. Tables: `owners` & `beneficial_ownership`
Ultimate Beneficial Owner (UBO) structure for business entities.

### `owners`
| Column Name | Data Type | Nullable | Key / Constraint | Description |
|---|---|---|---|---|
| `owner_id` | VARCHAR(32) | No | PRIMARY KEY | Unique ID (e.g., `OWN-00001`) |
| `owner_reference` | VARCHAR(128) | No | UNIQUE INDEX | Synthetic identifier reference |
| `created_at` | DATETIME | No | DEFAULT CURRENT_TIMESTAMP | Audit timestamp |

### `beneficial_ownership`
| Column Name | Data Type | Nullable | Key / Constraint | Description |
|---|---|---|---|---|
| `ownership_id` | VARCHAR(32) | No | PRIMARY KEY | Identifier (e.g., `UBO-00001`) |
| `business_customer_id`| VARCHAR(32) | No | FOREIGN KEY -> `customers(customer_id)` | Business customer |
| `owner_id` | VARCHAR(32) | No | FOREIGN KEY -> `owners(owner_id)` | Beneficial owner |
| `ownership_percentage`| DECIMAL(5,2) | No | - | Ownership stake (e.g., 35.50%) |
| `effective_from` | DATE | No | - | Effective start date |
| `effective_to` | DATE | Yes | - | Effective end date |
| `verification_status` | VARCHAR(32) | No | INDEX | `VERIFIED`, `PENDING`, `DISCREPANCY` |

---

## 9. Table: `alerts`
Actionable notifications generated for expiring documents, overdue reviews, and missing evidence.

| Column Name | Data Type | Nullable | Key / Constraint | Description |
|---|---|---|---|---|
| `alert_id` | VARCHAR(32) | No | PRIMARY KEY | Identifier (e.g., `ALT-2026-000001`) |
| `customer_id` | VARCHAR(32) | No | FOREIGN KEY -> `customers(customer_id)` | Target customer |
| `document_id` | VARCHAR(32) | Yes | FOREIGN KEY -> `documents(document_id)` | Related document if applicable |
| `review_id` | VARCHAR(32) | Yes | FOREIGN KEY -> `review_cases(review_id)` | Related review if applicable |
| `alert_type` | VARCHAR(64) | No | INDEX | `DOCUMENT_EXPIRY_30D`, `DOCUMENT_EXPIRY_15D`, `DOCUMENT_EXPIRY_7D`, `DOCUMENT_EXPIRED`, `REVIEW_OVERDUE`, `BENEFICIAL_OWNERSHIP_OVER_100`, `MISSING_MANDATORY_EVIDENCE` |
| `severity` | VARCHAR(16) | No | INDEX | `LOW`, `MEDIUM`, `HIGH`, `CRITICAL` |
| `created_at` | DATETIME | No | INDEX | Generation timestamp |
| `due_at` | DATETIME | Yes | - | Remediation deadline |
| `alert_status` | VARCHAR(32) | No | INDEX | `OPEN`, `ACKNOWLEDGED`, `RESOLVED`, `DISMISSED` |
| `resolved_at` | DATETIME | Yes | - | When resolved |
| `resolution_notes` | TEXT | Yes | - | Remediation notes |

---

## 10. Table: `audit_events`
Immutable historical log of all state changes, decisions, approvals, and anomaly remediations.

| Column Name | Data Type | Nullable | Key / Constraint | Description |
|---|---|---|---|---|
| `audit_event_id` | BIGINT AUTO_INCREMENT | No | PRIMARY KEY | Sequential audit event identifier |
| `entity_type` | VARCHAR(64) | No | INDEX | `CUSTOMER`, `DOCUMENT`, `REVIEW`, `ALERT`, `BENEFICIAL_OWNERSHIP` |
| `entity_id` | VARCHAR(64) | No | INDEX | Affected entity identifier |
| `event_type` | VARCHAR(64) | No | INDEX | `STATUS_CHANGE`, `VERIFICATION_SUBMITTED`, `APPROVAL_GRANTED`, `APPROVAL_REJECTED`, `ANOMALY_RESOLVED`, `OWNERSHIP_UPDATED` |
| `actor_id` | VARCHAR(64) | No | INDEX | Actor username or automated service |
| `event_timestamp` | DATETIME | No | INDEX | Immutable event timestamp |
| `previous_values` | JSON / TEXT | Yes | - | Snapshot of entity state prior to change |
| `new_values` | JSON / TEXT | Yes | - | Snapshot of entity state after change |
| `reason` | TEXT | Yes | - | Business justification or reason code |
| `correlation_id` | VARCHAR(64) | Yes | INDEX | Distributed request tracing ID |
