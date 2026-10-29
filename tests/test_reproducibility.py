import unittest
from validation.reproducibility import test_reproducibility

class TestReproducibility(unittest.TestCase):
    def test_reproducible_sha256_checksums(self):
        res = test_reproducibility(seed=20261022, customers=50, documents=100, reviews=20)
        self.assertEqual(res["status"], "PASS")
        self.assertEqual(res["mismatches_count"], 0)
        self.assertGreater(res["files_verified"], 0)

if __name__ == "__main__":
    unittest.main()
