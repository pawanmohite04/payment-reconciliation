# Distilled Prompt

Build a small, explainable payment reconciliation application for a month-end finance use case.

## Objective
Compare a payment platform transaction ledger with bank settlement records and identify why the month-end totals do not agree.

## Required planted discrepancies
1. A platform transaction dated on the last day of the reporting month settles in the following month.
2. Several individually immaterial sub-cent amount differences accumulate into a material aggregate rounding variance.
3. One platform transaction appears more than once.
4. A refund exists but references an original payment that does not exist in the platform ledger.

## Functional requirements
- Generate deterministic sample CSV files for platform transactions and bank settlements.
- Validate required columns, dates, amounts and supported currency.
- Match using transaction ID and transaction type.
- Distinguish matched, late settlement, amount mismatch, duplicate, missing settlement and orphan refund.
- Use decimal arithmetic for money.
- Apply a per-transaction tolerance and a separate aggregate rounding tolerance.
- Show summary metrics, exception details and unmatched bank entries.
- Allow CSV downloads.
- Include automated tests for all planted issues and normal matching.
- Document assumptions and production limitations.

## Constraints
Use Python, Pandas and Streamlit. Keep the project understandable for a junior engineer, runnable locally in VS Code, and deployable on Streamlit Community Cloud. Do not claim that demo data or simplified rules are production-ready.
