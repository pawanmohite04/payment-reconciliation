import streamlit as st
import pandas as pd
from pathlib import Path
from generate_data import generate_sample_data
from reconciliation import reconcile, required_columns
from financial_bridge import build_financial_bridge

st.set_page_config(page_title="Payment Reconciliation", page_icon="💳", layout="wide")
st.title("💳 Payment Reconciliation Dashboard")
st.caption("Compare platform transactions with bank settlements and investigate month-end differences.")

with st.sidebar:
    st.header("Data")
    if st.button("Generate demo data", width="stretch"):
        tx, bank = generate_sample_data()
        tx.to_csv("data/transactions.csv", index=False)
        bank.to_csv("data/bank_settlements.csv", index=False)
        st.session_state["transactions"] = tx
        st.session_state["bank"] = bank
        st.success("Demo datasets generated.")

    tx_file = st.file_uploader("Upload platform transactions CSV", type=["csv"])
    bank_file = st.file_uploader("Upload bank settlements CSV", type=["csv"])
    st.divider()
    month = st.selectbox("Transaction month", ["2026-10", "2026-11"], index=0)
    row_tolerance = st.number_input("Per-transaction tolerance", min_value=0.0, value=0.005, step=0.001, format="%.3f")
    aggregate_tolerance = st.number_input("Aggregate rounding tolerance", min_value=0.0, value=0.01, step=0.001, format="%.3f")

if tx_file is not None and bank_file is not None:
    transactions = pd.read_csv(tx_file, dtype={"transaction_id": "string", "original_transaction_id": "string"})
    bank = pd.read_csv(bank_file, dtype={"transaction_id": "string", "original_transaction_id": "string"})
elif "transactions" in st.session_state and "bank" in st.session_state:
    transactions = st.session_state["transactions"].copy()
    bank = st.session_state["bank"].copy()
else:
    tx_path, bank_path = Path("data/transactions.csv"), Path("data/bank_settlements.csv")
    if tx_path.exists() and bank_path.exists():
        transactions, bank = pd.read_csv(tx_path), pd.read_csv(bank_path)
    else:
        transactions, bank = generate_sample_data()

for label, df in [("Platform transactions", transactions), ("Bank settlements", bank)]:
    missing = set(required_columns(label)) - set(df.columns)
    if missing:
        st.error(f"{label} is missing required columns: {', '.join(sorted(missing))}")
        st.stop()

result = reconcile(
    transactions,
    bank,
    month=month,
    row_tolerance=row_tolerance,
    aggregate_tolerance=aggregate_tolerance,
)
summary = result["summary"]

bridge_result = build_financial_bridge(result)

st.divider()

st.header("Financial Reconciliation Bridge")

st.caption(
    "Understand the reasons behind the month-end "
    "difference between platform and bank records."
)

col1, col2 = st.columns(2)

with col1:
    st.metric(
        "Actual Month-End Difference",
        f"₹{bridge_result['actual_difference']:,.3f}"
    )

with col2:
    st.metric(
        "Explained Difference",
        f"₹{bridge_result['explained_difference']:,.3f}"
    )

st.dataframe(
    bridge_result["bridge"],
    use_container_width=True,
    hide_index=True
)

if bridge_result["is_balanced"]:
    st.success(
        "Financial bridge balanced! "
        "All month-end differences are explained."
    )
else:
    st.warning(
        "Financial bridge has an unexplained difference. "
        "Further investigation is required."
    )

st.subheader(f"Reconciliation overview — {month}")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Platform records", summary["platform_records"])
c2.metric("Unique platform transactions", summary["unique_platform_transactions"])
c3.metric("Matched / within tolerance", summary["matched"])
c4.metric("Exceptions", summary["exceptions"])

c5, c6, c7, c8 = st.columns(4)
c5.metric("Platform net amount", f"₹{summary['platform_net']:,.3f}")
c6.metric("Bank net amount in month", f"₹{summary['bank_net_in_month']:,.3f}")
c7.metric("Month-end difference", f"₹{summary['month_end_difference']:,.3f}")
c8.metric("Aggregate rounding variance", f"₹{summary['aggregate_rounding_variance']:,.3f}")

st.info("Assumptions: transaction IDs are the primary matching key; amounts are in INR; platform amounts may carry three decimal places; bank amounts are rounded to two decimals; the selected month is based on transaction date; settlements after month-end are shown as late settlements rather than missing forever.")

st.subheader("Exception breakdown")
counts = result["reconciliation"]["status"].value_counts().rename_axis("Status").reset_index(name="Count")
if counts.empty:
    st.success("No exceptions found.")
else:
    st.dataframe(counts, use_container_width=True, hide_index=True)

st.subheader("Transaction-level reconciliation")
view = result["reconciliation"]
st.dataframe(view, use_container_width=True, hide_index=True)

st.subheader("Bank entries without a corresponding platform record")
st.dataframe(result["unmatched_bank"], use_container_width=True, hide_index=True)

st.subheader("Aggregate rounding check")
st.write(result["rounding_summary"])
if summary["aggregate_rounding_flag"]:
    st.warning("Aggregate rounding variance exceeds the configured tolerance even though individual differences are within per-transaction tolerance.")
else:
    st.success("Aggregate rounding variance is within tolerance.")

csv = view.to_csv(index=False).encode("utf-8")
st.download_button("Download reconciliation CSV", csv, file_name=f"reconciliation_{month}.csv", mime="text/csv")
bank_csv = result["unmatched_bank"].to_csv(index=False).encode("utf-8")
st.download_button("Download unmatched bank entries", bank_csv, file_name="unmatched_bank_entries.csv", mime="text/csv")

with st.expander("View source datasets"):
    st.markdown("**Platform transactions**")
    st.dataframe(transactions, use_container_width=True, hide_index=True)
    st.markdown("**Bank settlements**")
    st.dataframe(bank, use_container_width=True, hide_index=True)
