
import pandas as pd


def build_financial_bridge(result):

    reconciliation = result["reconciliation"]
    unmatched_bank = result["unmatched_bank"]
    summary = result["summary"]

    late_settlements = reconciliation.loc[
        reconciliation["status"] == "LATE_SETTLEMENT",
        "platform_amount"
    ].sum()

    missing_settlements = reconciliation.loc[
        reconciliation["status"] == "MISSING_SETTLEMENT",
        "platform_amount"
    ].sum()

    amount_mismatches = reconciliation.loc[
        reconciliation["status"] == "AMOUNT_MISMATCH",
        "difference_platform_minus_bank"
    ].sum()

    rounding_variance = summary["aggregate_rounding_variance"]

    unmatched_bank_amount = unmatched_bank["amount"].sum()

    bridge = [
        {
            "Component": "Late settlements",
            "Adjustment": float(late_settlements),
            "Explanation": "Settled after month-end"
        },
        {
            "Component": "Missing settlements",
            "Adjustment": float(missing_settlements),
            "Explanation": "No bank settlement found"
        },
        {
            "Component": "Amount mismatches",
            "Adjustment": float(amount_mismatches),
            "Explanation": "Platform amount minus bank amount"
        },
        {
            "Component": "Rounding variance",
            "Adjustment": float(rounding_variance),
            "Explanation": "Accumulated individual rounding differences"
        },
        {
            "Component": "Unmatched bank entries",
            "Adjustment": float(-unmatched_bank_amount),
            "Explanation": "Bank entries without platform transactions"
        }
    ]

    bridge_df = pd.DataFrame(bridge)

    explained_difference = bridge_df["Adjustment"].sum()

    return {
        "bridge": bridge_df,
        "explained_difference": float(explained_difference),
        "actual_difference": summary["month_end_difference"],
        "is_balanced": abs(
            explained_difference -
            summary["month_end_difference"]
        ) < 0.000001
    }
