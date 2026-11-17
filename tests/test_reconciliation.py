
import unittest

from generate_data import generate_sample_data
from reconciliation import reconcile


class ReconciliationTests(unittest.TestCase):

    def setUp(self):
        self.tx, self.bank = generate_sample_data()

        self.result = reconcile(
            self.tx,
            self.bank,
            month="2026-10"
        )

        self.status = dict(
            zip(
                self.result["reconciliation"]["transaction_id"],
                self.result["reconciliation"]["status"]
            )
        )

    def test_normal_transactions_match(self):
        self.assertEqual(
            self.status["TXN-1001"],
            "MATCHED"
        )

        self.assertEqual(
            self.status["TXN-1002"],
            "MATCHED"
        )

    def test_next_month_settlement_is_late(self):
        self.assertEqual(
            self.status["TXN-LATE-01"],
            "LATE_SETTLEMENT"
        )

    def test_duplicate_platform_transaction_is_flagged(self):
        self.assertEqual(
            self.status["TXN-DUP-01"],
            "DUPLICATE"
        )

        self.assertEqual(
            self.result["summary"]["platform_records"],
            10
        )

        self.assertEqual(
            self.result["summary"]["unique_platform_transactions"],
            9
        )

    def test_orphan_refund_is_flagged(self):
        self.assertEqual(
            self.status["REF-ORPHAN-01"],
            "ORPHAN_REFUND"
        )

    def test_missing_settlement_is_flagged(self):
        self.assertEqual(
            self.status["TXN-MISSING-01"],
            "MISSING_SETTLEMENT"
        )

    def test_rounding_only_visible_in_aggregate(self):

        rounding_rows = self.result["reconciliation"][
            self.result["reconciliation"]["transaction_id"].str.startswith(
                "TXN-RND"
            )
        ]

        self.assertTrue(
            (rounding_rows["status"] == "MATCHED").all()
        )

        self.assertEqual(
            len(rounding_rows),
            3
        )

        self.assertAlmostEqual(
            self.result["summary"]["aggregate_rounding_variance"],
            0.012,
            places=6
        )

        self.assertTrue(
            self.result["summary"]["aggregate_rounding_flag"]
        )

    def test_unexpected_bank_entry_is_listed(self):

        ids = set(
            self.result["unmatched_bank"]["transaction_id"]
        )

        self.assertIn(
            "TXN-UNKNOWN-01",
            ids
        )

    def test_only_unknown_bank_entry_is_unmatched(self):

        unmatched_ids = set(
            self.result["unmatched_bank"]["transaction_id"]
        )

        self.assertEqual(
            unmatched_ids,
            {"TXN-UNKNOWN-01"}
        )


if __name__ == "__main__":
    unittest.main()
