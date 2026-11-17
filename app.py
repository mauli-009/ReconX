
import streamlit as st
import pandas as pd

from core.data_generator import generate_sample_data
from core.validator import validate_dataset
from core.reconciliation import reconcile


# =====================================================
# 1. PAGE CONFIGURATION
# =====================================================

st.set_page_config(
    page_title="ReconX | Payment Reconciliation",
    page_icon="💳",
    layout="wide",
    initial_sidebar_state="expanded"
)


# =====================================================
# 2. CUSTOM CSS
# =====================================================

st.markdown("""
<style>

.stApp {
    background-color: #0b1120;
    color: #f8fafc;
}

.block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
}

[data-testid="stMetric"] {
    background-color: #172033;
    padding: 18px;
    border-radius: 12px;
    border: 1px solid #263449;
}

[data-testid="stMetricLabel"] {
    color: #94a3b8;
}

[data-testid="stMetricValue"] {
    color: #ffffff;
}

h1, h2, h3 {
    color: #f8fafc;
}

div.stButton > button {
    border-radius: 8px;
    font-weight: 600;
}

</style>
""", unsafe_allow_html=True)


# =====================================================
# 3. SESSION STATE
# =====================================================

if "transactions" not in st.session_state:
    st.session_state.transactions = None

if "settlements" not in st.session_state:
    st.session_state.settlements = None

if "result" not in st.session_state:
    st.session_state.result = None


# =====================================================
# 4. HELPER FUNCTIONS
# =====================================================

def load_data(tx, bank):

    tx_errors = validate_dataset(
        tx,
        "transactions"
    )

    bank_errors = validate_dataset(
        bank,
        "settlements"
    )

    errors = tx_errors + bank_errors

    if errors:

        for error in errors:
            st.error(error)

        return False

    st.session_state.transactions = tx
    st.session_state.settlements = bank

    # Clear old reconciliation results
    st.session_state.result = None

    return True


def generate_data():

    try:

        tx, bank = generate_sample_data()

        if load_data(tx, bank):

            st.success(
                "Sample datasets generated successfully!"
            )

            st.write(
                f"Platform records: {len(tx)}"
            )

            st.write(
                f"Bank records: {len(bank)}"
            )

            return True

    except Exception as error:

        st.error(
            f"Dataset generation failed: {error}"
        )

    return False


def run_reconciliation(month):

    try:

        result = reconcile(
            st.session_state.transactions,
            st.session_state.settlements,
            month
        )

        st.session_state.result = result

        return True

    except Exception as error:

        st.error(
            f"Reconciliation failed: {error}"
        )

        return False


def format_inr(value):

    return f"₹{value}"


# =====================================================
# 5. SIDEBAR NAVIGATION
# =====================================================

st.sidebar.title("💳 ReconX")

st.sidebar.caption(
    "Intelligent Payment Reconciliation"
)

st.sidebar.divider()

page = st.sidebar.radio(
    "Navigation",
    [
        "Dashboard",
        "Upload Data",
        "Reconciliation",
        "Reports",
        "About"
    ]
)

st.sidebar.divider()

st.sidebar.markdown(
    "**System Status**"
)

if st.session_state.transactions is not None:

    st.sidebar.success("Datasets Loaded")

else:

    st.sidebar.warning("No Dataset Loaded")

if st.session_state.result is not None:

    st.sidebar.success("Reconciliation Complete")

else:

    st.sidebar.info("Awaiting Reconciliation")

st.sidebar.divider()

st.sidebar.caption("ReconX v2.0")
st.sidebar.caption("AI Native Engineer Assessment")


# =====================================================
# 6. DASHBOARD PAGE
# =====================================================

if page == "Dashboard":

    st.title("ReconX Financial Dashboard")

    st.caption(
        "Understand every difference between payment "
        "platform transactions and bank settlements."
    )

    st.divider()

    # -----------------------------------------------
    # No reconciliation available
    # -----------------------------------------------

    if st.session_state.result is None:

        st.info(
            "No reconciliation results available. "
            "Generate sample data or upload your own datasets."
        )

        if st.button(
            "Generate Sample Data",
            type="primary"
        ):

            generate_data()

    else:

        summary = st.session_state.result["summary"]

        issues = st.session_state.result["issues"]

        # -----------------------------------------------
        # TRANSACTION OVERVIEW
        # -----------------------------------------------

        st.subheader("Transaction Overview")

        c1, c2, c3, c4 = st.columns(4)

        c1.metric(
            "Platform Transactions",
            summary["total_platform_transactions"]
        )

        c2.metric(
            "Matched Transactions",
            summary["matched_transactions"]
        )

        c3.metric(
            "Total Discrepancies",
            summary["total_issues"]
        )

        c4.metric(
            "Reconciliation Period",
            summary["month"]
        )

        st.divider()

        # -----------------------------------------------
        # FINANCIAL INTELLIGENCE
        # -----------------------------------------------

        st.subheader("Financial Intelligence")

        c1, c2, c3 = st.columns(3)

        c1.metric(
            "Platform Payment Value",
            format_inr(
                summary["platform_payment_total"]
            )
        )

        c2.metric(
            "Bank Reported Value",
            format_inr(
                summary["bank_reported_total"]
            )
        )

        c3.metric(
            "Successfully Matched",
            format_inr(
                summary["matched_amount"]
            )
        )

        c4, c5, c6 = st.columns(3)

        c4.metric(
            "Late Settlements",
            format_inr(
                summary["late_settlement_amount"]
            )
        )

        c5.metric(
            "Duplicate Bank Value",
            format_inr(
                summary["duplicate_bank_amount"]
            )
        )

        c6.metric(
            "Under Investigation",
            format_inr(
                summary["under_investigation"]
            )
        )

        st.caption(
            "All amounts are INR. Amounts under investigation "
            "are not confirmed financial losses."
        )

        st.divider()

        # -----------------------------------------------
        # ROUNDING ANALYSIS
        # -----------------------------------------------

        st.subheader("Aggregate Rounding Analysis")

        r1, r2, r3 = st.columns(3)

        r1.metric(
            "Platform Aggregate",
            format_inr(summary["platform_total"])
        )

        r2.metric(
            "Bank Aggregate",
            format_inr(summary["bank_total"])
        )

        r3.metric(
            "Rounding Difference",
            format_inr(summary["rounding_difference"])
        )

        st.divider()

        # -----------------------------------------------
        # SEVERITY ANALYSIS
        # -----------------------------------------------

        st.subheader("Discrepancy Severity")

        if not issues.empty:

            severity_counts = (
                issues["severity"].value_counts()
            )

            a, b, c = st.columns(3)

            a.metric(
                "Critical",
                severity_counts.get("CRITICAL", 0)
            )

            b.metric(
                "Warnings",
                severity_counts.get("WARNING", 0)
            )

            c.metric(
                "Informational",
                severity_counts.get("INFO", 0)
            )

        else:

            st.success(
                "No discrepancies detected!"
            )

        st.divider()

        # -----------------------------------------------
        # DISCREPANCY DISTRIBUTION
        # -----------------------------------------------

        st.subheader("Discrepancy Distribution")

        if not issues.empty:

            chart_data = (
                issues["issue_type"]
                .value_counts()
                .rename_axis("Issue Type")
                .reset_index(name="Count")
            )

            st.bar_chart(
                chart_data.set_index("Issue Type")
            )

        else:

            st.info(
                "No discrepancy distribution available."
            )

        st.divider()

        # -----------------------------------------------
        # RECENT DISCREPANCIES
        # -----------------------------------------------

        st.subheader("Recent Discrepancies")

        if not issues.empty:

            st.dataframe(
                issues.head(10),
                use_container_width=True,
                hide_index=True
            )

        else:

            st.success(
                "All transactions are reconciled."
            )


# =====================================================
# 7. UPLOAD DATA PAGE
# =====================================================

elif page == "Upload Data":

    st.title("Upload Financial Data")

    st.caption(
        "Import platform transactions and bank settlements."
    )

    st.info(
        "Upload both CSV files using the required data schema."
    )

    # -----------------------------------------------
    # PLATFORM FILE
    # -----------------------------------------------

    st.subheader("Platform Transactions")

    tx_file = st.file_uploader(
        "Upload Platform Transactions CSV",
        type=["csv"],
        key="tx_file"
    )

    # -----------------------------------------------
    # BANK FILE
    # -----------------------------------------------

    st.subheader("Bank Settlements")

    bank_file = st.file_uploader(
        "Upload Bank Settlements CSV",
        type=["csv"],
        key="bank_file"
    )

    # -----------------------------------------------
    # VALIDATE AND LOAD
    # -----------------------------------------------

    if st.button(
        "Validate and Load Data",
        type="primary"
    ):

        if tx_file is None or bank_file is None:

            st.warning(
                "Please upload both CSV files."
            )

        else:

            try:

                tx = pd.read_csv(
                    tx_file,
                    dtype=str,
                    keep_default_na=False
                )

                bank = pd.read_csv(
                    bank_file,
                    dtype=str,
                    keep_default_na=False
                )

                if load_data(tx, bank):

                    st.success(
                        "Both datasets loaded successfully!"
                    )

                    st.subheader(
                        "Platform Transaction Preview"
                    )

                    st.dataframe(
                        tx.head(10),
                        use_container_width=True
                    )

                    st.subheader(
                        "Bank Settlement Preview"
                    )

                    st.dataframe(
                        bank.head(10),
                        use_container_width=True
                    )

            except Exception as error:

                st.error(
                    f"CSV processing failed: {error}"
                )

    st.divider()

    # -----------------------------------------------
    # SAMPLE DATA
    # -----------------------------------------------

    st.subheader("Try with Sample Data")

    if st.button("Generate Sample Dataset"):

        generate_data()


# =====================================================
# 8. RECONCILIATION PAGE
# =====================================================

elif page == "Reconciliation":

    st.title("Run Reconciliation")

    st.caption(
        "Compare platform transactions against bank settlements."
    )

    # -----------------------------------------------
    # CHECK DATA AVAILABILITY
    # -----------------------------------------------

    if (
        st.session_state.transactions is None
        or st.session_state.settlements is None
    ):

        st.warning(
            "Please upload datasets or generate sample data first."
        )

    else:

        st.success(
            "Both datasets are ready for reconciliation."
        )

        st.subheader("Reconciliation Configuration")

        month = st.selectbox(
            "Select Reconciliation Month",
            [
                "2026-11",
                "2026-12"
            ]
        )

        st.write(
            f"Platform records: "
            f"{len(st.session_state.transactions)}"
        )

        st.write(
            f"Bank records: "
            f"{len(st.session_state.settlements)}"
        )

        st.divider()

        if st.button(
            "Run Reconciliation",
            type="primary"
        ):

            with st.spinner(
                "Analyzing and matching transactions..."
            ):

                success = run_reconciliation(month)

            if success:

                st.success(
                    "Reconciliation completed successfully!"
                )

        # -----------------------------------------------
        # EXECUTION SUMMARY
        # -----------------------------------------------

        if st.session_state.result is not None:

            summary = st.session_state.result["summary"]

            st.subheader("Execution Summary")

            c1, c2, c3 = st.columns(3)

            c1.metric(
                "Total Transactions",
                summary["total_platform_transactions"]
            )

            c2.metric(
                "Matched",
                summary["matched_transactions"]
            )

            c3.metric(
                "Issues",
                summary["total_issues"]
            )

            st.write(
                f"Selected Period: {summary['month']}"
            )

            st.info(
                "Open the Dashboard for financial analysis "
                "or Reports for transaction-level details."
            )


# =====================================================
# 9. REPORTS PAGE
# =====================================================

elif page == "Reports":

    st.title("Reconciliation Reports")

    result = st.session_state.result

    if result is None:

        st.warning(
            "Run reconciliation before viewing reports."
        )

    else:

        matched = result["matched"]

        issues = result["issues"]

        # -----------------------------------------------
        # MATCHED TRANSACTIONS
        # -----------------------------------------------

        st.subheader("Matched Transactions")

        st.caption(
            f"Successfully matched: {len(matched)} records"
        )

        st.dataframe(
            matched,
            use_container_width=True,
            hide_index=True
        )

        st.download_button(
            "Download Matched Transactions",
            data=matched.to_csv(index=False),
            file_name="reconx_matched.csv",
            mime="text/csv"
        )

        st.divider()

        # -----------------------------------------------
        # DISCREPANCY REPORT
        # -----------------------------------------------

        st.subheader("Discrepancy Report")

        if not issues.empty:

            issue_types = sorted(
                issues["issue_type"].unique()
            )

            severities = sorted(
                issues["severity"].unique()
            )

            selected_types = st.multiselect(
                "Filter by Issue Type",
                issue_types,
                default=issue_types
            )

            selected_severities = st.multiselect(
                "Filter by Severity",
                severities,
                default=severities
            )

            filtered = issues[
                issues["issue_type"].isin(selected_types)
                &
                issues["severity"].isin(selected_severities)
            ]

            st.write(
                f"Showing {len(filtered)} of {len(issues)} discrepancies"
            )

            st.dataframe(
                filtered,
                use_container_width=True,
                hide_index=True
            )

            st.download_button(
                "Download Discrepancy Report",
                data=filtered.to_csv(index=False),
                file_name="reconx_discrepancies.csv",
                mime="text/csv"
            )

        else:

            st.success(
                "No discrepancies detected!"
            )

        st.divider()

        # -----------------------------------------------
        # DOWNLOAD COMPLETE SUMMARY
        # -----------------------------------------------

        st.subheader("Financial Summary Export")

        summary_df = pd.DataFrame(
            [
                {
                    "Metric": key,
                    "Value": value
                }
                for key, value in result["summary"].items()
            ]
        )

        st.dataframe(
            summary_df,
            use_container_width=True,
            hide_index=True
        )

        st.download_button(
            "Download Financial Summary",
            data=summary_df.to_csv(index=False),
            file_name="reconx_financial_summary.csv",
            mime="text/csv"
        )


# =====================================================
# 10. ABOUT PAGE
# =====================================================

elif page == "About":

    st.title("About ReconX")

    st.markdown("""
    ## Intelligent Payment Reconciliation Engine

    ReconX is a financial reconciliation application that
    compares payment platform transaction records with
    actual bank settlement records.

    ### Core Features

    - Automated transaction matching
    - Duplicate entry detection
    - Late settlement identification
    - Orphan refund detection
    - Aggregate rounding analysis
    - Financial discrepancy reporting
    - Severity classification
    - CSV report exports

    ### Technology Stack

    - Python
    - Streamlit
    - Pandas
    - Decimal
    - Pytest

    ### Financial Assumptions

    1. Initial currency is INR.
    2. Platform records transactions instantly.
    3. Bank settlements can occur after month end.
    4. Refunds reference original payment IDs.
    5. Monetary calculations use Decimal arithmetic.
    6. Bank records contain transaction references.
    7. Duplicate records are reported rather than silently removed.

    ### Production Limitations

    This prototype uses synthetic data and simplified matching rules.
    It does not yet integrate with live bank APIs or payment gateways.

    Production deployment would require stronger authentication,
    audit trails, partial settlement handling, chargeback processing,
    multi-currency support and operational monitoring.
    """)

    st.divider()

    st.caption(
        "ReconX | AI Native Engineer Assessment | November 2026"
    )
