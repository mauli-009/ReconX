
import pandas as pd
from decimal import Decimal, InvalidOperation


TRANSACTION_COLUMNS = {
    "transaction_id",
    "original_transaction_id",
    "transaction_date",
    "amount",
    "currency",
    "type",
}

SETTLEMENT_COLUMNS = {
    "settlement_id",
    "transaction_id",
    "settlement_date",
    "amount",
    "currency",
    "type",
}


def validate_dataset(df, dataset_type):
    errors = []

    # Validate the dataset type first.
    if dataset_type not in ("transactions", "settlements"):
        return ["Invalid dataset type. Use 'transactions' or 'settlements'."]

    if not isinstance(df, pd.DataFrame):
        return ["Input must be a pandas DataFrame."]

    required = (
        TRANSACTION_COLUMNS
        if dataset_type == "transactions"
        else SETTLEMENT_COLUMNS
    )

    missing = required - set(df.columns)

    if missing:
        errors.append(f"Missing columns: {sorted(missing)}")
        return errors

    if df.empty:
        return ["Dataset cannot be empty."]

    # Check required identifiers.
    if df["transaction_id"].isna().any() or (
        df["transaction_id"].astype("string").str.strip().eq("").any()
    ):
        errors.append("Transaction ID cannot be empty.")

    if dataset_type == "settlements":
        if df["settlement_id"].isna().any() or (
            df["settlement_id"].astype("string").str.strip().eq("").any()
        ):
            errors.append("Settlement ID cannot be empty.")

        settlement_ids = df["settlement_id"].astype("string").str.strip()

        if settlement_ids.duplicated().any():
            errors.append("Settlement IDs must be unique.")

    # Check currency.
    if df["currency"].isna().any() or (
        df["currency"].astype("string").str.strip().eq("").any()
    ):
        errors.append("Currency cannot be empty.")

    # Check transaction type.
    valid_types = {"PAYMENT", "REFUND"}
    transaction_types = (
        df["type"].astype("string").str.strip().str.upper()
    )

    if transaction_types.isna().any() or not transaction_types.isin(
        valid_types
    ).all():
        errors.append("Invalid transaction type. Use PAYMENT or REFUND.")

    # Validate amounts using Decimal to avoid floating-point surprises.
    for value in df["amount"]:
        try:
            if pd.isna(value) or str(value).strip() == "":
                raise InvalidOperation

            amount = Decimal(str(value).strip())

            if not amount.is_finite() or amount < 0:
                errors.append(f"Invalid amount: {value}")
                break

        except (InvalidOperation, ValueError, TypeError):
            errors.append(f"Invalid amount: {value}")
            break

    # Validate dates.
    date_column = (
        "transaction_date"
        if dataset_type == "transactions"
        else "settlement_date"
    )

    dates = pd.to_datetime(df[date_column], errors="coerce")

    if dates.isna().any():
        errors.append("Invalid date values.")

    return errors
