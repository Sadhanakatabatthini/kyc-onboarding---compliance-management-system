# KYC Onboarding & Compliance Management System

An enterprise-grade, end-to-end KYC Onboarding and Compliance Management System designed for tracking customer onboarding evidence, validating document completeness, managing risk ratings, scheduling periodic reviews, detecting document expirations, generating alerts, handling exceptions, and maintaining an immutable audit history.

---

## 1. System Architecture

```
Streamlit Frontend (Port 8501) ──HTTP REST──> Flask REST API (Port 5000) ──SQLAlchemy ORM──> MySQL 8.0 InnoDB
```

- **Frontend:** Streamlit multi-page interface (`app/streamlit_app.py`, `app/pages/`) with Plotly visualizations and role-based persona switching.
- **Backend:** Flask REST API (`backend/app.py`, `backend/routes/`) with OpenAPI specification (`/api/v1/docs`).
- **Database & ORM:** MySQL 8.0 with InnoDB engine, primary and foreign key constraints, unique indexes, transactions, and SQLAlchemy 2.0 ORM models (`backend/models/`).
- **Rules Engine:** Reusable business logic for KYC completeness %, onboarding gating, periodic review scheduling, expiry escalations, and independent anomaly discovery (`backend/rules/`).
- **Synthetic Data Generator:** Deterministic generator with fixed master seed `20261022`, supporting baseline volumes (8,000 customers, 1,000 businesses, 20,000 documents, 3,000 review cases) and 5 injected compliance anomalies (`generator/generate.py`).
- **Evaluation & Validation:** Independent detection engine discovering anomalies without ground truth access, computing Precision, Recall, F1 Score, False Positive Rate, and verifying SHA-256 seed reproducibility (`validation/`).

---

## 2. Setup and Execution Guide

### Prerequisites
- Python 3.10+
- MySQL Server 8.0+ (or local SQLite fallback)

### Step 1: Environment Setup
#### Windows (PowerShell / Command Prompt):
```powershell
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

#### Linux / macOS:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Step 2: Database Configuration
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Ensure your MySQL credentials are configured in `.env`:
```env
DATABASE_URL=mysql+pymysql://kyc_user:kyc_secure_password_2026@localhost:3306/kyc_compliance_db
```

### Step 3: Initialize Database Schema and Seeds
In MySQL CLI or Workbench:
```sql
SOURCE exports/kyc_schema.sql;
SOURCE exports/kyc_seeds.sql;
```

### Step 4: Generate Synthetic Datasets
Generate starter test batch (100 customers, 250 documents, 40 reviews):
```bash
python -m generator.generate --seed 20261022 --customers 100 --documents 250 --reviews 40
```

Generate full baseline evaluation dataset (8,000 customers, 1,000 business, 20,000 documents, 3,000 reviews):
```bash
python -m generator.generate --seed 20261022 --customers 8000 --business 1000 --documents 20000 --reviews 3000
```

### Step 5: Start Flask REST API Backend
```bash
python -m backend.app
# Backend runs at: http://localhost:5000
# OpenAPI specification: http://localhost:5000/api/v1/docs
```

### Step 6: Start Streamlit Frontend
In a new terminal:
```bash
streamlit run app/streamlit_app.py --server.port 8501
# Frontend opens at: http://localhost:8501
```

### Step 7: Run Automated Verification Tests
Run complete test suite using pytest or standard Python test runner:
```bash
# Using pytest
pytest tests/ -v

# Or using the zero-dependency test runner
python python_runner.py
```

### Step 8: Validate Evaluation Metrics and Checksums
```bash
# Evaluate precision, recall, and compliance metrics
python -m validation.metrics

# Verify relational integrity (PKs, FKs, null constraints)
python -m validation.integrity_checks

# Test SHA-256 reproducibility across multiple runs
python -m validation.reproducibility
```

---

## 3. The 5 Injected Anomaly Scenarios & Detection

| Anomaly ID | Name | Detection Logic | Ground Truth Label | Expected Action |
|---|---|---|---|---|
| `ANOMALY-001` | Expired Document Marked Valid | `expiry_date < TODAY AND document_status == 'VALID'` | `CRITICAL_ANOMALY` | Mark document EXPIRED |
| `ANOMALY-002` | Customer Approved Missing Evidence | `lifecycle_status == 'APPROVED' AND completeness < 100%` | `CRITICAL_ANOMALY` | Reopen review; revoke approval |
| `ANOMALY-003` | Ownership Percentage > 100% | $\sum \text{Ownership \%} > 100.00\%$ per business | `HIGH_ANOMALY` | Freeze account; require reconciliation |
| `ANOMALY-004` | Review Closed Without Resolution | `review_status == 'COMPLETED' AND (resolution_code IS NULL OR notes IS NULL)` | `HIGH_ANOMALY` | Reopen review; enforce resolution notes |
| `ANOMALY-005` | Duplicate Document Reference | Same reference used across distinct customers | `MEDIUM_ANOMALY` | Investigate fraud/collision |

---

## 4. Documentation Directory

- `docs/DATA_DICTIONARY.md`: Complete column definitions, data types, and nullability constraints.
- `docs/BUSINESS_RULES.md`: Mathematical KYC completeness formula, lifecycle state machine, review intervals, and RBAC matrix.
- `docs/ER_DIAGRAM.md`: Visual entity-relationship diagram and key mapping.
- `docs/GENERATOR.md`: Generation sequence, baseline volume distributions, and seed details.
- `docs/REPRODUCIBILITY.md`: Deterministic checksum comparison procedure.
- `exports/kyc_schema.sql`: MySQL 8.0 InnoDB DDL with foreign key integrity.
- `exports/kyc_seeds.sql`: Reference requirements and customer types.
