import unittest
from datetime import date
from backend.rules.anomaly_detector import detect_anomalies

class TestAnomalyDetector(unittest.TestCase):
    def test_detects_all_five_anomalies(self):
        eval_date = date(2026, 10, 28)

        # 1. Expired doc marked valid
        documents = [
            {
                "document_id": "DOC-EXP-01",
                "customer_id": "CUS-001",
                "document_type": "PASSPORT",
                "document_status": "VALID",  # Contradiction
                "expiry_date": "2026-05-01",
                "document_reference": "REF-100"
            },
            # 5. Duplicate document reference used by unrelated customer CUS-002
            {
                "document_id": "DOC-DUP-02",
                "customer_id": "CUS-002",
                "document_type": "PASSPORT",
                "document_status": "VALID",
                "expiry_date": "2028-05-01",
                "document_reference": "REF-100"  # Exact duplicate of DOC-EXP-01
            }
        ]

        # 2. Customer approved missing mandatory evidence
        customers = [
            {
                "customer_id": "CUS-001",
                "customer_type_id": 1,
                "lifecycle_status": "APPROVED"  # Missing address proof
            },
            {
                "customer_id": "CUS-002",
                "customer_type_id": 1,
                "lifecycle_status": "PENDING_VERIFICATION"
            },
            # 3. Business customer with > 100% ownership
            {
                "customer_id": "CUS-BIZ-003",
                "customer_type_id": 2,
                "lifecycle_status": "UNDER_REVIEW"
            }
        ]

        requirements = [
            {
                "requirement_id": "R1",
                "requirement_code": "PASSPORT",
                "customer_type_id": 1,
                "document_type": "PASSPORT",
                "mandatory_flag": True
            },
            {
                "requirement_id": "R2",
                "requirement_code": "ADDRESS",
                "customer_type_id": 1,
                "document_type": "PROOF_OF_ADDRESS",
                "mandatory_flag": True
            }
        ]

        # 3. Ownership > 100%
        beneficial_ownerships = [
            {"ownership_id": "UBO-1", "business_customer_id": "CUS-BIZ-003", "ownership_percentage": 60.0},
            {"ownership_id": "UBO-2", "business_customer_id": "CUS-BIZ-003", "ownership_percentage": 55.0}  # Sum = 115%
        ]

        # 4. Review closed without resolution
        review_cases = [
            {
                "review_id": "REV-001",
                "customer_id": "CUS-001",
                "review_status": "COMPLETED",
                "resolution_code": None,
                "resolution_notes": ""
            }
        ]

        detected = detect_anomalies(
            customers=customers,
            documents=documents,
            requirements=requirements,
            verifications=[],
            review_cases=review_cases,
            beneficial_ownerships=beneficial_ownerships,
            evaluation_date=eval_date
        )

        detected_types = {d["anomaly_type"] for d in detected}
        self.assertIn("EXPIRED_DOCUMENT_MARKED_VALID", detected_types)
        self.assertIn("APPROVED_MISSING_MANDATORY_EVIDENCE", detected_types)
        self.assertIn("OWNERSHIP_PERCENTAGE_EXCEEDS_100", detected_types)
        self.assertIn("REVIEW_CLOSED_WITHOUT_RESOLUTION", detected_types)
        self.assertIn("DUPLICATE_DOCUMENT_REFERENCE", detected_types)

if __name__ == "__main__":
    unittest.main()
