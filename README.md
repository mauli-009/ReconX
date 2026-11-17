
# ReconX — Intelligent Payment Reconciliation System

ReconX is a payment reconciliation application that compares transactions recorded by a payment platform with settlement records received from a bank.

It identifies discrepancies, highlights suspicious records, and provides financial summaries to help investigate why the platform's books do not balance.

## Problem Statement

A payment company maintains two datasets:

1. Platform transactions — records of payments and refunds processed by the platform.
2. Bank settlements — records of funds reported as settled by the bank.

Ideally, both datasets should agree. However, timing differences, duplicate records, rounding differences, and unmatched refunds can cause discrepancies.

ReconX automates the comparison and highlights these issues.

## Key Features

- Generate synthetic platform and bank datasets.
- Upload platform transaction and bank settlement CSV files.
- Validate input data before reconciliation.
- Match transactions using transaction ID, type, and currency.
- Detect late settlements.
- Detect duplicate bank settlement entries.
- Detect refunds without a corresponding original transaction.
- Detect aggregate rounding differences.
- Classify discrepancies by severity.
- Display matched transactions and discrepancy reports.
- Download reconciliation results as CSV files.

## Technology Stack

| Component | Technology |
|---|---|
| Programming language | Python |
| User interface | Streamlit |
| Data processing | Pandas |
| Financial precision | Decimal |
| Testing | Pytest |
| Data input | CSV |

## Project Structure

```text
reconx/
│
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
│
├── core/
│   ├── __init__.py
│   ├── data_generator.py
│   ├── validator.py
│   └── reconciliation.py
│
├── tests/
│   ├── __init__.py
│   ├── test_reconciliation.py
│   └── test_validator.py
│
└── data/
    └── .gitkeep
```

## How Reconciliation Works

### 1. Data ingestion

The application accepts two CSV datasets:

- Platform transactions
- Bank settlements

### 2. Data validation

The validator checks:

- Required columns
- Missing transaction IDs
- Missing settlement IDs
- Duplicate settlement IDs
- Invalid amounts
- Invalid dates
- Invalid transaction types
- Missing currencies

### 3. Transaction matching

The reconciliation engine compares records using:

- Transaction ID
- Transaction type
- Currency
- Transaction amount

### 4. Discrepancy detection

The application identifies the following scenarios:

| Scenario | Description |
|---|---|
| Late settlement | A platform transaction is settled after the reporting month. |
| Aggregate rounding | Individually rounded records produce a different total from rounding the aggregate amount. |
| Duplicate settlement | A transaction appears more than once in bank settlement records. |
| Orphan refund | A refund refers to an original transaction that cannot be found. |

### 5. Reporting

The application displays:

- Matched transactions
- Unmatched transactions
- Discrepancy types
- Severity classification
- Financial summaries
- Downloadable CSV reports

## Running the Project Locally

### Step 1: Clone the repository

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
cd reconx
```

### Step 2: Create a virtual environment

```bash
python -m venv venv
```

### Step 3: Activate the environment

Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

### Step 4: Install dependencies

```bash
pip install -r requirements.txt
```

### Step 5: Start the application

```bash
streamlit run app.py
```

The application will open in your browser.

## Running Tests

Run the complete test suite:

```bash
pytest -v
```

The current test suite contains 19 tests:

- 7 reconciliation tests
- 12 data validation tests

Latest local test result: 19 passed.

## Synthetic Data and Assumptions

The sample dataset intentionally contains four discrepancies:

1. A platform transaction dated in November that settles in December.
2. Multiple small rounding differences that create an aggregate difference.
3. A duplicate bank settlement entry.
4. A refund referencing a nonexistent original transaction.

Additional assumptions:

- Transaction IDs are used as the primary matching reference.
- Currency and transaction type must agree for a match.
- Amounts are processed using decimal arithmetic to reduce floating-point errors.
- The reporting month is selected by the user.
- Duplicate settlement IDs are rejected during input validation.
- The synthetic dataset is designed for demonstration and testing, not production accounting.

## Production Limitations

1. **Partial settlements:** The current matching logic does not fully support one transaction being settled through multiple legitimate bank entries. A production system should support split settlements and many-to-one matching.

2. **Data scale and reliability:** CSV-based processing is suitable for a demonstration but may not scale to high-volume payment systems. A production implementation should use reliable database storage, incremental processing, and job orchestration.

3. **Security and auditability:** The current application is a prototype and does not implement enterprise-grade authentication, role-based access control, encryption, immutable audit logs, or regulatory compliance controls.

## Future Improvements

- Support partial and split settlements.
- Add configurable reconciliation rules.
- Introduce database-backed transaction storage.
- Add audit trails and investigation workflows.
- Add authentication and role-based access.
- Support scheduled reconciliation.
- Add scalable processing for large datasets.

## Project Status

The current prototype implements synthetic data generation, CSV validation, reconciliation, discrepancy classification, reporting, and automated tests.

It is intended as a demonstration of payment reconciliation logic and is not yet a production-ready financial accounting system.
