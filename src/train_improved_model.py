import duckdb
import pandas as pd
import numpy as np
import joblib
import os

from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    average_precision_score,
    roc_auc_score
)

DATABASE = "data/fraud_risk.duckdb"

print("\nTRAINING IMPROVED FRAUD MODEL")
print("=" * 65)

con = duckdb.connect(DATABASE)


# --------------------------------------------------
# 1. CREATE RECENT TRAINING WINDOW
# --------------------------------------------------

recent_start = con.execute("""
SELECT quantile_cont(transaction_time, 0.60)
FROM transactions_clean
""").fetchone()[0]

test_start = con.execute("""
SELECT quantile_cont(transaction_time, 0.80)
FROM transactions_clean
""").fetchone()[0]

print("\nRecent training starts:", recent_start)
print("Future testing starts:", test_start)


# --------------------------------------------------
# 2. FEATURES
# --------------------------------------------------

features = """

    b.absolute_amount,
    b.is_refund,

    b.is_online,
    b.is_chip,
    b.is_swipe,

    b.transaction_hour,
    b.day_of_week,
    b.has_error,

    CAST(b.has_chip AS INTEGER) AS card_has_chip,
    b.card_on_dark_web,

    b.credit_limit,
    b.amount_to_credit_limit,

    b.credit_score,
    b.yearly_income,
    b.total_debt,
    b.num_credit_cards,

    h.customer_previous_avg,
    h.card_previous_avg,
    h.amount_vs_customer_avg,
    h.amount_vs_card_avg

"""


# --------------------------------------------------
# 3. RECENT TRAINING DATA
# --------------------------------------------------

print("\n1. Loading recent training data...")

train_query = f"""
SELECT
    {features},
    b.is_fraud

FROM model_features_basic b

JOIN behavior_features h
    ON b.transaction_id = h.transaction_id

JOIN transactions_clean t
    ON b.transaction_id = t.transaction_id

WHERE
    t.transaction_time >= ?
    AND t.transaction_time < ?
    AND hash(b.transaction_id) % 100 < 35
"""

train_df = con.execute(
    train_query,
    [recent_start, test_start]
).fetchdf()

print(f"Training rows: {len(train_df):,}")
print(f"Fraud cases: {int(train_df['is_fraud'].sum()):,}")


# --------------------------------------------------
# 4. FUTURE TEST DATA
# --------------------------------------------------

print("\n2. Loading future test data...")

test_query = f"""
SELECT
    {features},
    b.is_fraud

FROM model_features_basic b

JOIN behavior_features h
    ON b.transaction_id = h.transaction_id

JOIN transactions_clean t
    ON b.transaction_id = t.transaction_id

WHERE
    t.transaction_time >= ?
    AND hash(b.transaction_id) % 100 < 25
"""

test_df = con.execute(
    test_query,
    [test_start]
).fetchdf()

con.close()

print(f"Test rows: {len(test_df):,}")
print(f"Fraud cases: {int(test_df['is_fraud'].sum()):,}")


# --------------------------------------------------
# 5. X AND Y
# --------------------------------------------------

X_train = train_df.drop(columns=["is_fraud"])
y_train = train_df["is_fraud"]

X_test = test_df.drop(columns=["is_fraud"])
y_test = test_df["is_fraud"]


# --------------------------------------------------
# 6. FILL MISSING VALUES
# --------------------------------------------------

imputer = SimpleImputer(strategy="median")

X_train_clean = imputer.fit_transform(X_train)
X_test_clean = imputer.transform(X_test)


# --------------------------------------------------
# 7. GIVE FRAUD MORE IMPORTANCE
# --------------------------------------------------

fraud_weight = 40

sample_weights = np.where(
    y_train == 1,
    fraud_weight,
    1
)


# --------------------------------------------------
# 8. TRAIN STRONGER MODEL
# --------------------------------------------------

print("\n3. Training improved model...")

model = HistGradientBoostingClassifier(
    learning_rate=0.08,
    max_iter=200,
    max_leaf_nodes=31,
    random_state=42
)

model.fit(
    X_train_clean,
    y_train,
    sample_weight=sample_weights
)

print("Model trained.")


# --------------------------------------------------
# 9. FRAUD PROBABILITIES
# --------------------------------------------------

fraud_probability = model.predict_proba(
    X_test_clean
)[:, 1]


# --------------------------------------------------
# 10. TEST DEFAULT THRESHOLD
# --------------------------------------------------

threshold = 0.50

predictions = (
    fraud_probability >= threshold
).astype(int)


print("\nCLASSIFICATION REPORT")
print("-" * 65)

print(
    classification_report(
        y_test,
        predictions,
        digits=4
    )
)


print("\nCONFUSION MATRIX")
print("-" * 65)

print(
    confusion_matrix(
        y_test,
        predictions
    )
)


print("\nMODEL SCORES")
print("-" * 65)

print(
    "PR-AUC:",
    round(
        average_precision_score(
            y_test,
            fraud_probability
        ),
        4
    )
)

print(
    "ROC-AUC:",
    round(
        roc_auc_score(
            y_test,
            fraud_probability
        ),
        4
    )
)


# --------------------------------------------------
# 11. SAVE EVERYTHING
# --------------------------------------------------

os.makedirs("models", exist_ok=True)

joblib.dump(
    {
        "model": model,
        "imputer": imputer,
        "features": list(X_train.columns)
    },
    "models/improved_fraud_model.joblib"
)

print(
    "\nSaved to "
    "models/improved_fraud_model.joblib"
)