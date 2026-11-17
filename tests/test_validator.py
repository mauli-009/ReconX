
import pandas as pd

from core.validator import validate_dataset


def valid_transactions():
    return pd.DataFrame({
        "transaction_id": ["TXN001"],
        "original_transaction_id": [""],
        "transaction_date": ["2026-11-10"],
        "amount": ["100.00"],
        "currency": ["INR"],
        "type": ["PAYMENT"],
    })


def valid_settlements():
    return pd.DataFrame({
        "settlement_id": ["SET001"],
        "transaction_id": ["TXN001"],
        "settlement_date": ["2026-11-11"],
        "amount": ["100.00"],
        "currency": ["INR"],
        "type": ["PAYMENT"],
    })


def test_valid_transaction_dataset():
    assert validate_dataset(
        valid_transactions(), "transactions"
    ) == []


def test_valid_settlement_dataset():
    assert validate_dataset(
        valid_settlements(), "settlements"
    ) == []


def test_missing_required_column():
    df = valid_transactions().drop(columns=["amount"])

    errors = validate_dataset(df, "transactions")

    assert any("Missing columns" in error for error in errors)


def test_empty_transaction_id():
    df = valid_transactions()
    df.loc[0, "transaction_id"] = "   "

    errors = validate_dataset(df, "transactions")

    assert "Transaction ID cannot be empty." in errors


def test_invalid_amount():
    df = valid_transactions()
    df.loc[0, "amount"] = "abc"

    errors = validate_dataset(df, "transactions")

    assert any("Invalid amount" in error for error in errors)


def test_negative_amount():
    df = valid_transactions()
    df.loc[0, "amount"] = "-100"

    errors = validate_dataset(df, "transactions")

    assert any("Invalid amount" in error for error in errors)


def test_invalid_date():
    df = valid_transactions()
    df.loc[0, "transaction_date"] = "not-a-date"

    errors = validate_dataset(df, "transactions")

    assert "Invalid date values." in errors


def test_duplicate_settlement_ids():
    df = valid_settlements()
    duplicate = df.copy()
    df = pd.concat([df, duplicate], ignore_index=True)

    errors = validate_dataset(df, "settlements")

    assert "Settlement IDs must be unique." in errors


def test_empty_dataset():
    df = valid_transactions().iloc[0:0]

    errors = validate_dataset(df, "transactions")

    assert "Dataset cannot be empty." in errors


def test_invalid_dataset_type():
    errors = validate_dataset(valid_transactions(), "unknown")

    assert any("Invalid dataset type" in error for error in errors)


def test_invalid_transaction_type():
    df = valid_transactions()
    df.loc[0, "type"] = "UNKNOWN"

    errors = validate_dataset(df, "transactions")

    assert any("Invalid transaction type" in error for error in errors)


def test_empty_currency():
    df = valid_transactions()
    df.loc[0, "currency"] = " "

    errors = validate_dataset(df, "transactions")

    assert "Currency cannot be empty." in errors
