
import pandas as pd


def generate_sample_data():
    transactions = [
        ["TXN-1001", "payment", "2026-10-02", 100.00, "INR", ""],
        ["TXN-1002", "payment", "2026-10-05", 250.50, "INR", ""],
        ["TXN-LATE-01", "payment", "2026-10-31", 5000.00, "INR", ""],
        ["TXN-RND-01", "payment", "2026-10-20", 10.004, "INR", ""],
        ["TXN-RND-02", "payment", "2026-10-20", 10.004, "INR", ""],
        ["TXN-RND-03", "payment", "2026-10-20", 10.004, "INR", ""],
        ["TXN-DUP-01", "payment", "2026-10-22", 75.00, "INR", ""],
        ["TXN-DUP-01", "payment", "2026-10-22", 75.00, "INR", ""],
        ["TXN-MISSING-01", "payment", "2026-10-25", 125.00, "INR", ""],
        ["REF-ORPHAN-01", "refund", "2026-10-27", -800.00, "INR", "TXN-DOES-NOT-EXIST"],
    ]

    bank = [
        ["SET-2001", "TXN-1001", "payment", "2026-10-03", 100.00, "INR", ""],
        ["SET-2002", "TXN-1002", "payment", "2026-10-06", 250.50, "INR", ""],
        ["SET-LATE-01", "TXN-LATE-01", "payment", "2026-11-01", 5000.00, "INR", ""],
        ["SET-RND-01", "TXN-RND-01", "payment", "2026-10-21", 10.00, "INR", ""],
        ["SET-RND-02", "TXN-RND-02", "payment", "2026-10-21", 10.00, "INR", ""],
        ["SET-RND-03", "TXN-RND-03", "payment", "2026-10-21", 10.00, "INR", ""],
        ["SET-DUP-01", "TXN-DUP-01", "payment", "2026-10-23", 75.00, "INR", ""],
        ["SET-REF-01", "REF-ORPHAN-01", "refund", "2026-10-28", -800.00, "INR", "TXN-DOES-NOT-EXIST"],
        ["SET-UNEXPECTED-01", "TXN-UNKNOWN-01", "payment", "2026-10-29", 42.00, "INR", ""],
    ]

    tx_cols = [
        "transaction_id",
        "transaction_type",
        "transaction_date",
        "amount",
        "currency",
        "original_transaction_id"
    ]

    bank_cols = [
        "settlement_id",
        "transaction_id",
        "entry_type",
        "settlement_date",
        "amount",
        "currency",
        "original_transaction_id"
    ]

    return (
        pd.DataFrame(transactions, columns=tx_cols),
        pd.DataFrame(bank, columns=bank_cols)
    )


if __name__ == "__main__":
    tx, bank = generate_sample_data()

    tx.to_csv("data/transactions.csv", index=False)
    bank.to_csv("data/bank_settlements.csv", index=False)

    print(f"Generated {len(tx)} platform rows and {len(bank)} bank rows.")
