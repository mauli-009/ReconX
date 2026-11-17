
import pytest

from core.data_generator import generate_sample_data
from core.reconciliation import reconcile


@pytest.fixture
def result():

    tx, bank = generate_sample_data()

    return reconcile(tx, bank, "2026-11")


def test_late_settlement(result):

    assert "LATE_SETTLEMENT" in (
        result["issues"]["issue_type"].values
    )


def test_duplicate_bank(result):

    assert "DUPLICATE_BANK_SETTLEMENT" in (
        result["issues"]["issue_type"].values
    )


def test_orphan_refund(result):

    assert "ORPHAN_REFUND" in (
        result["issues"]["issue_type"].values
    )


def test_rounding_difference(result):

    assert "AGGREGATE_ROUNDING_DIFFERENCE" in (
        result["issues"]["issue_type"].values
    )


def test_normal_transactions_match(result):

    assert len(result["matched"]) >= 20


def test_duplicate_not_silently_matched(result):

    matched = result["matched"]

    assert "TXN001" not in matched["transaction_id"].values


def test_summary(result):

    assert result["summary"]["total_platform_transactions"] == 25
