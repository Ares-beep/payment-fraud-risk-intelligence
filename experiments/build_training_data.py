import json
import csv
import duckdb
from pathlib import Path

TRANSACTIONS = "data/transactions_data.csv"
FRAUD_JSON = "data/train_fraud_labels.json"
FRAUD_CSV = "data/fraud_labels.csv"

print("\nBUILDING FRAUD TRAINING DATA")
print("=" * 60)


# --------------------------------------------------
# STEP 1: Convert fraud JSON into a simple CSV
# --------------------------------------------------

print("\n1. Converting fraud labels to CSV...")

with open(FRAUD_JSON, "r") as file:
    data = json.load(file)

labels = data["target"]

with open(FRAUD_CSV, "w", newline="") as file:
    writer = csv.writer(file)

    writer.writerow([
        "transaction_id",
        "is_fraud"
    ])

    for transaction_id, label in labels.items():

        writer.writerow([
            transaction_id,
            1 if label == "Yes" else 0
        ])

print(f"Created: {FRAUD_CSV}")
print(f"Labels written: {len(labels):,}")


# --------------------------------------------------
# STEP 2: Join transactions with fraud labels
# --------------------------------------------------

print("\n2. Joining transactions with fraud labels...")

query = f"""

SELECT

    t.id,
    t.date,
    t.client_id,
    t.card_id,
    t.amount,
    t.use_chip,
    t.merchant_id,
    t.merchant_city,
    t.merchant_state,
    t.zip,
    t.mcc,
    t.errors,

    f.is_fraud

FROM read_csv_auto(
    '{TRANSACTIONS}',
    quote='"',
    escape='"'
) t

INNER JOIN read_csv_auto(
    '{FRAUD_CSV}'
) f

ON t.id = f.transaction_id

"""

training_data = duckdb.sql(query)


# --------------------------------------------------
# STEP 3: Check joined dataset
# --------------------------------------------------

print("\n3. Join results")
print("-" * 60)

result = duckdb.sql(f"""

SELECT

    COUNT(*) AS joined_transactions,

    SUM(f.is_fraud) AS fraudulent_transactions

FROM read_csv_auto(
    '{TRANSACTIONS}',
    quote='"',
    escape='"'
) t

INNER JOIN read_csv_auto(
    '{FRAUD_CSV}'
) f

ON t.id = f.transaction_id

""")

print(result)


# --------------------------------------------------
# STEP 4: Show example fraudulent transactions
# --------------------------------------------------

print("\n4. Example fraudulent transactions")
print("-" * 60)

fraud_examples = duckdb.sql(query + """

WHERE f.is_fraud = 1

LIMIT 10

""")

print(fraud_examples)