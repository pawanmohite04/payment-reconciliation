
import unittest

from generate_data import generate_sample_data
from reconciliation import reconcile
from financial_bridge import build_financial_bridge


class TestFinancialBridge(unittest.TestCase):

    def test_financial_bridge_balances(self):
        platform, bank = generate_sample_data()

        result = reconcile(
            platform,
            bank,
            "2026-10",
            0.005,
            0.01
        )

        bridge = build_financial_bridge(result)

        self.assertTrue(bridge["is_balanced"])

        self.assertAlmostEqual(
            bridge["actual_difference"],
            5083.012,
            places=3
        )

        self.assertAlmostEqual(
            bridge["explained_difference"],
            5083.012,
            places=3
        )


if __name__ == "__main__":
    unittest.main()
