
from decimal import Decimal, ROUND_HALF_UP
from collections import Counter
import pandas as pd


# ==========================================
# CONFIGURATION
# ==========================================

CENT = Decimal("0.01")


# ==========================================
# MONEY UTILITIES
# ==========================================

def money(value):
    return Decimal(str(value))


def round_money(value):
    return value.quantize(
        CENT,
        rounding=ROUND_HALF_UP
    )


def decimal_sum(values):
    return sum(values, Decimal("0"))


# ==========================================
# MAIN RECONCILIATION ENGINE
# ==========================================

def reconcile(transactions, settlements, month="2026-11"):

    tx = transactions.copy()
    bank = settlements.copy()

    # --------------------------------------
    # 1. PREPROCESS DATA
    # --------------------------------------

    tx["transaction_date"] = pd.to_datetime(
        tx["transaction_date"],
        errors="raise"
    )

    bank["settlement_date"] = pd.to_datetime(
        bank["settlement_date"],
        errors="raise"
    )

    tx["amount_decimal"] = tx["amount"].apply(money)
    bank["amount_decimal"] = bank["amount"].apply(money)

    start = pd.Timestamp(f"{month}-01")
    end_exclusive = start + pd.offsets.MonthBegin(1)

    # Select platform transactions for the month
    tx = tx[
        (tx["transaction_date"] >= start) &
        (tx["transaction_date"] < end_exclusive)
    ].copy()

    # Include bank settlements for:
    # 1. Transactions recorded in selected month.
    # 2. Settlements received during selected month.

    relevant_ids = set(tx["transaction_id"])

    bank = bank[
        (
            bank["transaction_id"].isin(relevant_ids)
        ) |
        (
            (bank["settlement_date"] >= start) &
            (bank["settlement_date"] < end_exclusive)
        )
    ].copy()

    # --------------------------------------
    # 2. INITIALIZE RESULTS
    # --------------------------------------

    issues = []
    matched = []

    # --------------------------------------
    # 3. ISSUE CLASSIFICATION
    # --------------------------------------

    severity_map = {
        "DUPLICATE_BANK_SETTLEMENT": "CRITICAL",
        "DUPLICATE_PLATFORM_TRANSACTION": "CRITICAL",
        "ORPHAN_REFUND": "CRITICAL",
        "MISSING_SETTLEMENT": "CRITICAL",
        "AMOUNT_MISMATCH": "CRITICAL",

        "LATE_SETTLEMENT": "WARNING",
        "SETTLEMENT_DATE_OUTSIDE_PERIOD": "WARNING",
        "AGGREGATE_ROUNDING_DIFFERENCE": "WARNING",
        "UNRECOGNIZED_BANK_ENTRY": "WARNING"
    }

    def issue(tid, kind, description, amount=None):

        issues.append({
            "transaction_id": tid,
            "issue_type": kind,
            "severity": severity_map.get(kind, "INFO"),
            "description": description,
            "amount": str(amount) if amount is not None else None
        })

    # --------------------------------------
    # 4. DETECT DUPLICATE PLATFORM RECORDS
    # --------------------------------------

    tx_counts = Counter(tx["transaction_id"])

    duplicate_tx = {
        tid
        for tid, count in tx_counts.items()
        if count > 1
    }

    for tid in duplicate_tx:

        issue(
            tid,
            "DUPLICATE_PLATFORM_TRANSACTION",
            "Repeated transaction ID in platform ledger."
        )

    # --------------------------------------
    # 5. DETECT DUPLICATE BANK RECORDS
    # --------------------------------------

    bank_counts = Counter(
        zip(
            bank["transaction_id"],
            bank["type"],
            bank["currency"]
        )
    )

    duplicate_bank = {
        key
        for key, count in bank_counts.items()
        if count > 1
    }

    for tid, typ, currency in duplicate_bank:

        issue(
            tid,
            "DUPLICATE_BANK_SETTLEMENT",
            "Multiple bank records exist for this transaction."
        )

    # --------------------------------------
    # 6. CREATE BANK LOOKUP
    # --------------------------------------

    lookup = {}

    for _, row in bank.iterrows():

        key = (
            row["transaction_id"],
            row["type"],
            row["currency"]
        )

        lookup.setdefault(key, []).append(row)

    payment_ids = set(
        tx.loc[
            tx["type"] == "PAYMENT",
            "transaction_id"
        ]
    )

    matched_bank_ids = set()

    # Store matched payment pairs for rounding analysis
    rounding_pairs = []

    # --------------------------------------
    # 7. PROCESS PLATFORM TRANSACTIONS
    # --------------------------------------

    for _, row in tx.iterrows():

        tid = row["transaction_id"]
        typ = row["type"]

        # Skip ambiguous duplicate platform records
        if tid in duplicate_tx:
            continue

        # ----------------------------------
        # ORPHAN REFUND DETECTION
        # ----------------------------------

        if typ == "REFUND":

            original = row["original_transaction_id"]

            if pd.isna(original) or original not in payment_ids:

                issue(
                    tid,
                    "ORPHAN_REFUND",
                    f"Original payment {original} does not exist.",
                    row["amount_decimal"]
                )

                continue

        # ----------------------------------
        # FIND CORRESPONDING BANK RECORD
        # ----------------------------------

        key = (
            tid,
            typ,
            row["currency"]
        )

        candidates = lookup.get(key, [])

        if not candidates:

            issue(
                tid,
                "MISSING_SETTLEMENT",
                "No matching bank settlement found.",
                row["amount_decimal"]
            )

            continue

        # Multiple records are ambiguous
        if len(candidates) > 1:
            continue

        settlement = candidates[0]

        # ----------------------------------
        # COMPARE AMOUNTS
        # ----------------------------------

        platform_amount = round_money(
            row["amount_decimal"]
        )

        bank_amount = round_money(
            settlement["amount_decimal"]
        )

        if platform_amount != bank_amount:

            difference = platform_amount - bank_amount

            issue(
                tid,
                "AMOUNT_MISMATCH",
                "Individual transaction amounts differ.",
                difference
            )

            continue

        matched_bank_ids.add(
            settlement["settlement_id"]
        )

        # ----------------------------------
        # CHECK SETTLEMENT DATE
        # ----------------------------------

        settlement_date = settlement["settlement_date"]

        if settlement_date >= end_exclusive:

            issue(
                tid,
                "LATE_SETTLEMENT",
                f"Settled on {settlement_date.date()}, after month end.",
                row["amount_decimal"]
            )

            continue

        if settlement_date < start:

            issue(
                tid,
                "SETTLEMENT_DATE_OUTSIDE_PERIOD",
                "Settlement occurred before the selected month."
            )

            continue

        # ----------------------------------
        # SUCCESSFUL MATCH
        # ----------------------------------

        matched.append({

            "transaction_id": tid,

            "type": typ,

            "currency": row["currency"],

            "transaction_amount": str(
                row["amount_decimal"]
            ),

            "settlement_amount": str(
                settlement["amount_decimal"]
            ),

            "transaction_date": str(
                row["transaction_date"].date()
            ),

            "settlement_date": str(
                settlement_date.date()
            ),

            "status": "MATCHED"
        })

        # Keep payment records for rounding analysis
        if typ == "PAYMENT":

            rounding_pairs.append((
                row["amount_decimal"],
                settlement["amount_decimal"]
            ))

    # --------------------------------------
    # 8. DETECT UNRECOGNIZED BANK ENTRIES
    # --------------------------------------

    for _, row in bank.iterrows():

        if row["settlement_id"] in matched_bank_ids:
            continue

        key = (
            row["transaction_id"],
            row["type"],
            row["currency"]
        )

        # Already classified as duplicate
        if key in duplicate_bank:
            continue

        # Late settlements are classified separately
        if row["settlement_date"] >= end_exclusive:
            continue

        issue(
            row["transaction_id"],
            "UNRECOGNIZED_BANK_ENTRY",
            "Bank record has no corresponding eligible platform transaction.",
            row["amount_decimal"]
        )

    # --------------------------------------
    # 9. AGGREGATE ROUNDING ANALYSIS
    # --------------------------------------

    platform_raw = decimal_sum(
        [p for p, b in rounding_pairs]
    )

    bank_raw = decimal_sum(
        [b for p, b in rounding_pairs]
    )

    platform_total = round_money(platform_raw)

    bank_total = round_money(bank_raw)

    rounding_difference = (
        platform_total - bank_total
    )

    if rounding_difference != Decimal("0.00"):

        issue(
            "AGGREGATE",
            "AGGREGATE_ROUNDING_DIFFERENCE",
            "Individually rounded amounts match, but aggregate totals differ.",
            rounding_difference
        )

    # --------------------------------------
    # 10. FINANCIAL INTELLIGENCE SUMMARY
    # --------------------------------------

    # Total platform payment value
    platform_payments = tx[
        tx["type"] == "PAYMENT"
    ]

    platform_payment_total = decimal_sum(
        platform_payments["amount_decimal"]
    )

    # Bank payments settled within selected month
    bank_payments = bank[
        (bank["type"] == "PAYMENT") &
        (bank["settlement_date"] >= start) &
        (bank["settlement_date"] < end_exclusive)
    ]

    # Total reported bank value including duplicates
    bank_reported_total = decimal_sum(
        bank_payments["amount_decimal"]
    )

    # Remove repeated transaction references
    bank_unique_payments = bank_payments.drop_duplicates(
        ["transaction_id", "type", "currency"],
        keep="first"
    )

    bank_unique_total = decimal_sum(
        bank_unique_payments["amount_decimal"]
    )

    # Amount successfully matched
    matched_payment_rows = [
        item
        for item in matched
        if item["type"] == "PAYMENT"
    ]

    matched_amount = decimal_sum(
        [
            money(item["transaction_amount"])
            for item in matched_payment_rows
        ]
    )

    # --------------------------------------
    # LATE SETTLEMENT VALUE
    # --------------------------------------

    late_ids = {
        item["transaction_id"]
        for item in issues
        if item["issue_type"] == "LATE_SETTLEMENT"
    }

    late_amount = decimal_sum(
        platform_payments.loc[
            platform_payments["transaction_id"].isin(late_ids),
            "amount_decimal"
        ]
    )

    # --------------------------------------
    # DUPLICATE BANK VALUE
    # --------------------------------------

    duplicate_bank_amount = (
        bank_reported_total - bank_unique_total
    )

    # --------------------------------------
    # AMOUNT REQUIRING INVESTIGATION
    # --------------------------------------

    under_investigation = (
        platform_payment_total
        - matched_amount
        - late_amount
    )

    # --------------------------------------
    # FORMAT FINANCIAL SUMMARY
    # --------------------------------------

    financial_summary = {

        "platform_payment_total": str(
            round_money(platform_payment_total)
        ),

        "bank_reported_total": str(
            round_money(bank_reported_total)
        ),

        "bank_unique_total": str(
            round_money(bank_unique_total)
        ),

        "matched_amount": str(
            round_money(matched_amount)
        ),

        "late_settlement_amount": str(
            round_money(late_amount)
        ),

        "duplicate_bank_amount": str(
            round_money(duplicate_bank_amount)
        ),

        "under_investigation": str(
            round_money(under_investigation)
        )
    }

    # --------------------------------------
    # 11. BUILD FINAL DATAFRAMES
    # --------------------------------------

    matched_df = pd.DataFrame(
        matched,
        columns=[
            "transaction_id",
            "type",
            "currency",
            "transaction_amount",
            "settlement_amount",
            "transaction_date",
            "settlement_date",
            "status"
        ]
    )

    issue_df = pd.DataFrame(
        issues,
        columns=[
            "transaction_id",
            "issue_type",
            "severity",
            "description",
            "amount"
        ]
    )

    # --------------------------------------
    # 12. FINAL SUMMARY
    # --------------------------------------

    summary = {

        "month": month,

        "total_platform_transactions": len(tx),

        "matched_transactions": len(matched_df),

        "total_issues": len(issue_df),

        "platform_total": str(platform_total),

        "bank_total": str(bank_total),

        "rounding_difference": str(rounding_difference),

        **financial_summary
    }

    # --------------------------------------
    # 13. RETURN RESULTS
    # --------------------------------------

    return {

        "summary": summary,

        "matched": matched_df,

        "issues": issue_df
    }
