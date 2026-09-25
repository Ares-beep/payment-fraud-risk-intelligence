import json
from collections import Counter

FRAUD_LABELS = "data/train_fraud_labels.json"

print("\nFRAUD LABEL ANALYSIS")
print("=" * 50)

# Load fraud labels
with open(FRAUD_LABELS, "r") as file:
    data = json.load(file)

labels = data["target"]

# Count Yes and No
counts = Counter(labels.values())

total = len(labels)
fraud = counts["Yes"]
legitimate = counts["No"]

fraud_rate = (fraud / total) * 100

print(f"\nTotal labelled transactions: {total:,}")
print(f"Legitimate transactions:     {legitimate:,}")
print(f"Fraudulent transactions:     {fraud:,}")
print(f"Fraud rate:                  {fraud_rate:.4f}%")

# Show a few fraudulent transaction IDs
fraud_ids = [
    transaction_id
    for transaction_id, label in labels.items()
    if label == "Yes"
]

print("\nExample fraudulent transaction IDs:")
for transaction_id in fraud_ids[:10]:
    print(transaction_id)