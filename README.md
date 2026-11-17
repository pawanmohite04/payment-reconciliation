# Payment Reconciliation Dashboard

A small, deterministic demo for the Onelab AI Fitness Assessment. It compares a payment platform ledger with bank settlement records and flags month-end discrepancies.

## Features
- Generates reproducible sample platform and bank CSV datasets.
- Matches records by transaction ID.
- Flags next-month settlements, duplicate platform records, missing settlements, amount mismatches, and refunds without an original payment.
- Checks sub-cent rounding differences per row and in aggregate.
- Shows unmatched bank entries and exports CSV results.

## Assumptions
1. The selected reporting month is based on the platform transaction date.
2. Transaction IDs are the primary matching key and are unique in a clean platform ledger.
3. The demo supports INR only; amounts are stored as decimal-like values and compared with Python `Decimal`.
4. Platform amounts may have three decimal places because of allocation/fee calculations; bank settlement amounts are rounded to two decimal places.
5. A per-transaction difference up to ₹0.005 is accepted for matching, but the sum of these differences is separately checked against ₹0.01.
6. Settlements after month-end are looked up in the supplied bank dataset and shown as `LATE_SETTLEMENT`.
7. Refunds must reference an existing original platform payment. A refund without one is `ORPHAN_REFUND`, even if the bank has a matching refund line.
8. Duplicate platform rows are flagged and only the first occurrence is counted in the unique-transaction total.
9. This is a demonstration dataset, not a production accounting policy.

## Run locally (Windows / VS Code)
Open this folder in VS Code. In the integrated terminal:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
py -m pip install -r requirements.txt
py generate_data.py
py -m unittest discover -s tests -v
streamlit run app.py
```

If PowerShell blocks activation, run:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.venv\Scripts\Activate.ps1
```

Open the local URL printed by Streamlit, usually http://localhost:8501.

## Deploy on Streamlit Community Cloud
1. Create a GitHub repository and upload this project.
2. Go to https://share.streamlit.io/ and sign in with GitHub.
3. Choose the repository, branch, and `app.py`.
4. Deploy. Keep the repository public if using the free deployment path and do not upload real customer data or secrets.

## Suggested demo video (2–3 minutes)
1. Show the dashboard and assumptions.
2. Generate the sample data.
3. Point out a normal matched payment.
4. Show the late settlement dated November 1.
5. Show the three rounding rows individually matched and the aggregate ₹0.012 variance.
6. Show the duplicate, missing settlement, orphan refund, and unmatched bank record.
7. Download the reconciliation CSV.

## Production limitations (three sentences)
The demo assumes transaction IDs are stable and globally unique, which may fail when processors reuse IDs or when one payment is split across multiple settlement lines. It does not model partial settlements, fees, chargebacks, reversals, multi-currency FX, bank holidays, or complex refund lifecycles. A production system would require authenticated ingestion, schema/version controls, immutable audit trails, role-based access, alerting, retry/idempotency controls, and reconciliation policies approved by Finance.

## Test coverage
Run `py -m unittest discover -s tests -v`. Tests cover normal matching, late settlement, rounding accumulation, duplicate platform rows, orphan refunds, missing settlements, and unmatched bank entries.
