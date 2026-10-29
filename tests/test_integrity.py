import unittest
from validation.integrity_checks import run_integrity_checks

class TestDataIntegrity(unittest.TestCase):
    def test_database_integrity_zero_violations(self):
        res = run_integrity_checks(data_dir="data/generated")
        self.assertEqual(res["status"], "PASS")
        self.assertEqual(res["pk_violations_count"], 0)
        self.assertEqual(res["fk_violations_count"], 0)
        self.assertEqual(res["null_violations_count"], 0)

if __name__ == "__main__":
    unittest.main()
