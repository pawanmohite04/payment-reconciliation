
from decimal import Decimal, InvalidOperation
import pandas as pd

PLATFORM_COLUMNS = [
    "transaction_id",
    "transaction_type",
    "transaction_date",
    "amount",
    "currency",
    "original_transaction_id"
]

BANK_COLUMNS = [
    "settlement_id",
    "transaction_id",
    "entry_type",
    "settlement_date",
    "amount",
    "currency",
    "original_transaction_id"
]


def required_columns(label):
    return (
        PLATFORM_COLUMNS
        if label == "Platform transactions"
        else BANK_COLUMNS
    )


def money(value):
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError(f"Invalid monetary value: {value!r}")


def reconcile(
    transactions,
    bank,
    month="2026-10",
    row_tolerance=0.005,
    aggregate_tolerance=0.01
):

    tx = transactions.copy()
    bk = bank.copy()

    # 1. Validate required columns

    missing_tx = set(PLATFORM_COLUMNS) - set(tx.columns)
    missing_bank = set(BANK_COLUMNS) - set(bk.columns)

    if missing_tx:
        raise ValueError(
            f"Missing platform columns: {missing_tx}"
        )

    if missing_bank:
        raise ValueError(
            f"Missing bank columns: {missing_bank}"
        )

    # 2. Validate dates

    tx["transaction_date"] = pd.to_datetime(
        tx["transaction_date"],
        errors="coerce"
    )

    bk["settlement_date"] = pd.to_datetime(
        bk["settlement_date"],
        errors="coerce"
    )

    if tx["transaction_date"].isna().any():
        raise ValueError("Invalid platform transaction date.")

    if bk["settlement_date"].isna().any():
        raise ValueError("Invalid bank settlement date.")

    # 3. Validate amounts

    if tx["amount"].isna().any() or bk["amount"].isna().any():
        raise ValueError("Amount cannot be empty.")

    tx["amount_decimal"] = tx["amount"].map(money)
    bk["amount_decimal"] = bk["amount"].map(money)

    # 4. Normalize identifiers and transaction types

    tx["transaction_id"] = (
        tx["transaction_id"].astype(str).str.strip()
    )

    bk["transaction_id"] = (
        bk["transaction_id"].astype(str).str.strip()
    )

    tx["transaction_type"] = (
        tx["transaction_type"].astype(str).str.lower().str.strip()
    )

    bk["entry_type"] = (
        bk["entry_type"].astype(str).str.lower().str.strip()
    )

    if tx["transaction_id"].eq("").any():
        raise ValueError("Platform transaction ID cannot be empty.")

    if bk["transaction_id"].eq("").any():
        raise ValueError("Bank transaction ID cannot be empty.")

    if not tx["transaction_type"].isin(["payment", "refund"]).all():
        raise ValueError("Invalid platform transaction type.")

    if not bk["entry_type"].isin(["payment", "refund"]).all():
        raise ValueError("Invalid bank entry type.")

    if (
        tx["currency"].astype(str).str.upper() != "INR"
    ).any() or (
        bk["currency"].astype(str).str.upper() != "INR"
    ).any():
        raise ValueError("This application currently supports INR only.")

    # 5. Define reporting month

    month_start = pd.Period(month, freq="M").start_time
    next_month_start = (
        pd.Period(month, freq="M") + 1
    ).start_time

    tx_month = tx[
        (tx["transaction_date"] >= month_start) &
        (tx["transaction_date"] < next_month_start)
    ].copy()

    bank_month = bk[
        (bk["settlement_date"] >= month_start) &
        (bk["settlement_date"] < next_month_start)
    ].copy()

    # 6. Detect duplicate platform transactions

    duplicate_ids = set(
        tx_month.loc[
            tx_month.duplicated(
                subset=["transaction_id"],
                keep="first"
            ),
            "transaction_id"
        ]
    )

    unique_tx = tx_month.drop_duplicates(
        subset=["transaction_id"],
        keep="first"
    ).copy()

    # 7. Identify valid original payment IDs

    platform_payment_ids = set(
        unique_tx.loc[
            unique_tx["transaction_type"] == "payment",
            "transaction_id"
        ]
    )

    # 8. Group bank records by transaction ID

    bank_groups = {
        key: group
        for key, group in bk.groupby("transaction_id")
    }

    rows = []
    rounding_differences = []

    # 9. Reconcile each platform transaction

    for _, row in unique_tx.iterrows():

        tid = row["transaction_id"]
        tx_type = row["transaction_type"]
        tx_amount = row["amount_decimal"]

        expected_entry = (
            "refund" if tx_type == "refund" else "payment"
        )

        matches = bank_groups.get(
            tid,
            pd.DataFrame()
        )

        if not matches.empty:
            matches = matches[
                matches["entry_type"] == expected_entry
            ]

        in_month_matches = matches[
            (matches["settlement_date"] >= month_start) &
            (matches["settlement_date"] < next_month_start)
        ] if not matches.empty else matches

        status = ""
        bank_amount = None
        settlement_date = None
        difference = None
        note = ""

        # Duplicate platform transaction

        if tid in duplicate_ids:

            status = "DUPLICATE"
            note = (
                "Repeated transaction ID in platform dataset; "
                "counted once."
            )

        # Refund without original payment

        elif (
            tx_type == "refund"
            and str(row["original_transaction_id"]).strip()
            not in platform_payment_ids
        ):

            status = "ORPHAN_REFUND"
            note = (
                "Refund has no matching original payment "
                "in the platform dataset."
            )

        # No settlement in reporting month

        elif in_month_matches.empty:

            later = matches[
                matches["settlement_date"] >= next_month_start
            ] if not matches.empty else matches

            if not later.empty:

                chosen = later.sort_values(
                    "settlement_date"
                ).iloc[0]

                bank_amount = chosen["amount_decimal"]

                settlement_date = (
                    chosen["settlement_date"].date().isoformat()
                )

                difference = float(
                    tx_amount - bank_amount
                )

                status = "LATE_SETTLEMENT"

                note = (
                    "Settlement occurred after the selected "
                    "reporting month."
                )

            else:

                status = "MISSING_SETTLEMENT"

                note = (
                    "No corresponding bank settlement was found."
                )

        # Settlement exists in reporting month

        else:

            chosen = in_month_matches.sort_values(
                "settlement_date"
            ).iloc[0]

            bank_amount = chosen["amount_decimal"]

            settlement_date = (
                chosen["settlement_date"].date().isoformat()
            )

            difference_decimal = tx_amount - bank_amount

            difference = float(difference_decimal)

            if abs(difference_decimal) > money(row_tolerance):

                status = "AMOUNT_MISMATCH"

                note = (
                    "Transaction and bank amounts differ "
                    "beyond per-transaction tolerance."
                )

            else:

                status = "MATCHED"

                note = (
                    "Matched by transaction ID and amount "
                    "within tolerance."
                )

                if difference_decimal != Decimal("0"):
                    rounding_differences.append(
                        difference_decimal
                    )

        rows.append({
            "transaction_id": tid,
            "transaction_type": tx_type,
            "transaction_date": (
                row["transaction_date"].date().isoformat()
            ),
            "platform_amount": float(tx_amount),
            "bank_amount": (
                float(bank_amount)
                if bank_amount is not None
                else None
            ),
            "settlement_date": settlement_date,
            "difference_platform_minus_bank": difference,
            "status": status,
            "investigation_note": note
        })

    # 10. Calculate aggregate rounding variance

    rounding_total = sum(
        rounding_differences,
        Decimal("0")
    )

    aggregate_flag = (
        abs(rounding_total) > money(aggregate_tolerance)
    )

    if aggregate_flag:

        for item in rows:

            if (
                item["status"] == "MATCHED"
                and item["difference_platform_minus_bank"] is not None
                and item["difference_platform_minus_bank"] != 0
            ):

                item["investigation_note"] += (
                    " Individual variance is within tolerance; "
                    "included in aggregate rounding check."
                )

    # 11. Identify genuinely unmatched bank entries

    platform_keys = set(
        zip(
            tx_month["transaction_id"],
            tx_month["transaction_type"].map(
                lambda t: "refund" if t == "refund" else "payment"
            )
        )
    )

    bank_keys = list(
        zip(
            bank_month["transaction_id"],
            bank_month["entry_type"]
        )
    )

    unmatched_bank = bank_month[
        [
            key not in platform_keys
            for key in bank_keys
        ]
    ].copy()

    unmatched_bank = unmatched_bank.drop(
        columns=["amount_decimal"],
        errors="ignore"
    )

    unmatched_bank["settlement_date"] = (
        unmatched_bank["settlement_date"].dt.date.astype(str)
    )

    # 12. Create reconciliation dataframe

    result = pd.DataFrame(rows)

    # 13. Calculate financial summary

    platform_net = sum(
        unique_tx["amount_decimal"],
        Decimal("0")
    )

    bank_net = sum(
        bank_month["amount_decimal"],
        Decimal("0")
    )

    exceptions = (
        int((result["status"] != "MATCHED").sum())
        if not result.empty
        else 0
    )

    summary = {

        "platform_records": int(len(tx_month)),

        "unique_platform_transactions": int(len(unique_tx)),

        "matched": (
            int((result["status"] == "MATCHED").sum())
            if not result.empty
            else 0
        ),

        "exceptions": exceptions,

        "platform_net": float(platform_net),

        "bank_net_in_month": float(bank_net),

        "month_end_difference": float(
            platform_net - bank_net
        ),

        "aggregate_rounding_variance": float(rounding_total),

        "aggregate_rounding_flag": bool(aggregate_flag)
    }

    # 14. Rounding report

    rounding_summary = pd.DataFrame([{

        "transactions_with_sub_cent_variance": len(
            rounding_differences
        ),

        "summed_platform_minus_bank_variance": float(
            rounding_total
        ),

        "configured_aggregate_tolerance": float(
            money(aggregate_tolerance)
        ),

        "aggregate_variance_flagged": bool(
            aggregate_flag
        )

    }])

    # 15. Return all reconciliation results

    return {

        "reconciliation": result,

        "unmatched_bank": unmatched_bank,

        "summary": summary,

        "rounding_summary": rounding_summary

    }
