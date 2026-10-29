import unittest
from datetime import date
from backend.rules.completeness import calculate_kyc_completeness, ConfigurationException
from backend.rules.onboarding import evaluate_onboarding_approval, can_transition_status

class TestKYCCompletenessAndOnboarding(unittest.TestCase):
    def setUp(self):
        self.requirements = [
            {
                "requirement_id": "KYC-01",
                "requirement_code": "PASSPORT",
                "customer_type_id": 1,
                "applicable_risk_level": "ALL",
                "document_type": "PASSPORT",
                "mandatory_flag": True,
                "effective_from": "2024-01-01",
                "effective_to": None,
                "active_status": True
            },
            {
                "requirement_id": "KYC-02",
                "requirement_code": "ADDRESS",
                "customer_type_id": 1,
                "applicable_risk_level": "ALL",
                "document_type": "PROOF_OF_ADDRESS",
                "mandatory_flag": True,
                "effective_from": "2024-01-01",
                "effective_to": None,
                "active_status": True
            }
        ]

    def test_completeness_calculation_partial_and_full(self):
        customer = {"customer_id": "CUS-TEST-01", "customer_type_id": 1, "risk_level": "LOW"}
        
        # 1 doc provided (Passport)
        docs = [
            {
                "document_id": "DOC-01",
                "customer_id": "CUS-TEST-01",
                "document_type": "PASSPORT",
                "document_status": "VALID",
                "expiry_date": "2028-12-31"
            }
        ]
        verifications = [{"document_id": "DOC-01", "verification_status": "PASSED"}]

        pct, satisfied, missing = calculate_kyc_completeness(
            customer, self.requirements, docs, verifications, as_of_date=date(2026, 10, 28)
        )
        self.assertEqual(pct, 50.0)
        self.assertEqual(len(satisfied), 1)
        self.assertEqual(len(missing), 1)

        # Add second doc (Proof of Address)
        docs.append({
            "document_id": "DOC-02",
            "customer_id": "CUS-TEST-01",
            "document_type": "PROOF_OF_ADDRESS",
            "document_status": "VALID",
            "expiry_date": "2026-11-30"
        })
        verifications.append({"document_id": "DOC-02", "verification_status": "PASSED"})

        pct_full, sat_full, miss_full = calculate_kyc_completeness(
            customer, self.requirements, docs, verifications, as_of_date=date(2026, 10, 28)
        )
        self.assertEqual(pct_full, 100.0)
        self.assertEqual(len(sat_full), 2)
        self.assertEqual(len(miss_full), 0)

    def test_approval_gating_blocks_incomplete_evidence(self):
        customer = {"customer_id": "CUS-TEST-01", "customer_type_id": 1, "risk_level": "LOW"}
        missing_reqs = [{"requirement_code": "PROOF_OF_ADDRESS", "mandatory_flag": True}]
        
        eligible, reasons = evaluate_onboarding_approval(
            customer=customer,
            completeness_percentage=50.0,
            missing_requirements=missing_reqs,
            reviewer_role="Risk / Compliance Reviewer"
        )
        self.assertFalse(eligible)
        self.assertTrue(any("completeness is 50.0%" in r for r in reasons))

    def test_unauthorized_role_rejected(self):
        customer = {"customer_id": "CUS-TEST-01", "customer_type_id": 1, "risk_level": "LOW"}
        eligible, reasons = evaluate_onboarding_approval(
            customer=customer,
            completeness_percentage=100.0,
            missing_requirements=[],
            reviewer_role="Operations Analyst"  # Not authorized
        )
        self.assertFalse(eligible)
        self.assertTrue(any("not authorized" in r for r in reasons))

    def test_valid_lifecycle_transitions(self):
        self.assertTrue(can_transition_status("PENDING_EVIDENCE", "PENDING_VERIFICATION"))
        self.assertTrue(can_transition_status("UNDER_REVIEW", "APPROVED"))
        self.assertFalse(can_transition_status("PENDING_EVIDENCE", "APPROVED"))  # Direct jump disallowed

if __name__ == "__main__":
    unittest.main()
