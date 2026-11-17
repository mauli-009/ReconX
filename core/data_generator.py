
import pandas as pd
import random
from datetime import datetime, timedelta


def generate_sample_data(seed=42):
    random.seed(seed)

    transactions = []
    settlements = []

    base_date = datetime(2026, 11, 1)

    # Generate 20 normal transactions
    for i in range(1, 21):
        transaction_id = f"TXN{i:03d}"
        amount = round(random.uniform(100, 5000), 2)

        transaction_date = base_date + timedelta(
            days=random.randint(0, 25)
        )

        settlement_date = transaction_date + timedelta(days=1)

        transactions.append({
            "transaction_id": transaction_id,
            "original_transaction_id": None,
            "transaction_date": transaction_date.strftime("%Y-%m-%d"),
            "amount": f"{amount:.2f}",
            "currency": "INR",
            "type": "PAYMENT"
        })

        settlements.append({
            "settlement_id": f"SET{i:03d}",
            "transaction_id": transaction_id,
            "settlement_date": settlement_date.strftime("%Y-%m-%d"),
            "amount": f"{amount:.2f}",
            "currency": "INR",
            "type": "PAYMENT"
        })

    # GAP 1: November transaction settled in December
    transactions.append({
        "transaction_id": "TXN021",
        "original_transaction_id": None,
        "transaction_date": "2026-11-30",
        "amount": "2500.00",
        "currency": "INR",
        "type": "PAYMENT"
    })

    settlements.append({
        "settlement_id": "SET021",
        "transaction_id": "TXN021",
        "settlement_date": "2026-12-02",
        "amount": "2500.00",
        "currency": "INR",
        "type": "PAYMENT"
    })

    # GAP 2: Duplicate bank entry for TXN001
    settlements.append({
        "settlement_id": "SET022",
        "transaction_id": "TXN001",
        "settlement_date": "2026-11-03",
        "amount": transactions[0]["amount"],
        "currency": "INR",
        "type": "PAYMENT"
    })

    # GAP 3: Refund with nonexistent original transaction
    transactions.append({
        "transaction_id": "REF001",
        "original_transaction_id": "TXN999",
        "transaction_date": "2026-11-18",
        "amount": "500.00",
        "currency": "INR",
        "type": "REFUND"
    })

    # GAP 4: Rounding discrepancy
    # Platform records 0.005 three times.
    # Bank records 0.01 three times.
    for i in range(22, 25):

        transaction_id = f"TXN{i:03d}"

        transactions.append({
            "transaction_id": transaction_id,
            "original_transaction_id": None,
            "transaction_date": "2026-11-20",
            "amount": "0.005",
            "currency": "INR",
            "type": "PAYMENT"
        })

        settlements.append({
            "settlement_id": f"SET{i+1:03d}",
            "transaction_id": transaction_id,
            "settlement_date": "2026-11-21",
            "amount": "0.01",
            "currency": "INR",
            "type": "PAYMENT"
        })

    return pd.DataFrame(transactions), pd.DataFrame(settlements)


if __name__ == "__main__":

    transactions, settlements = generate_sample_data()

    transactions.to_csv(
        "data/transactions.csv",
        index=False
    )

    settlements.to_csv(
        "data/settlements.csv",
        index=False
    )

    print("Datasets generated successfully!")
    print("Platform transactions:", len(transactions))
    print("Bank settlements:", len(settlements))
