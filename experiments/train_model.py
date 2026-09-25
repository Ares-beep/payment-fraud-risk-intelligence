import duckdb
import pandas as pd
import joblib
import os

from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import SGDClassifier

from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    average_precision_score,
    roc_auc_score
)


DATABASE = "data/fraud_risk.duckdb"

print("\nTRAINING PAYMENT FRAUD MODEL")
print("=" * 60)

con = duckdb.connect(DATABASE)


# --------------------------------------------------
# 1. FIND A TIME SPLIT
# --------------------------------------------------

print("\n1. Creating past vs future split...")

cutoff = con.execute("""
SELECT quantile_cont(transaction_time, 0.80)
FROM transactions_clean
""").fetchone()[0]

print("Training/test cutoff:", cutoff)


# --------------------------------------------------
# 2. FEATURES WE WILL GIVE THE MODEL
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
# 3. LOAD TRAINING DATA
# --------------------------------------------------

print("\n2. Loading training sample...")

train_query = f"""
SELECT
    {features},
    b.is_fraud

FROM model_features_basic b

INNER JOIN behavior_features h
    ON b.transaction_id = h.transaction_id

INNER JOIN transactions_clean t
    ON b.transaction_id = t.transaction_id

WHERE
    t.transaction_time < ?
    AND hash(b.transaction_id) % 100 < 15
"""

train_df = con.execute(
    train_query,
    [cutoff]
).fetchdf()

print(f"Training rows: {len(train_df):,}")
print(
    f"Training fraud cases: "
    f"{int(train_df['is_fraud'].sum()):,}"
)


# --------------------------------------------------
# 4. LOAD TEST DATA
# --------------------------------------------------

print("\n3. Loading future test sample...")

test_query = f"""
SELECT
    {features},
    b.is_fraud

FROM model_features_basic b

INNER JOIN behavior_features h
    ON b.transaction_id = h.transaction_id

INNER JOIN transactions_clean t
    ON b.transaction_id = t.transaction_id

WHERE
    t.transaction_time >= ?
    AND hash(b.transaction_id) % 100 < 25
"""

test_df = con.execute(
    test_query,
    [cutoff]
).fetchdf()

con.close()

print(f"Test rows: {len(test_df):,}")
print(
    f"Test fraud cases: "
    f"{int(test_df['is_fraud'].sum()):,}"
)


# --------------------------------------------------
# 5. SEPARATE INPUTS FROM THE ANSWER
# --------------------------------------------------

X_train = train_df.drop(columns=["is_fraud"])
y_train = train_df["is_fraud"]

X_test = test_df.drop(columns=["is_fraud"])
y_test = test_df["is_fraud"]


# --------------------------------------------------
# 6. BUILD THE MODEL
# --------------------------------------------------

print("\n4. Training baseline fraud model...")

model = Pipeline([

    (
        "fill_missing_values",
        SimpleImputer(strategy="median")
    ),

    (
        "scale_features",
        StandardScaler()
    ),

    (
        "classifier",
        SGDClassifier(
            loss="log_loss",
            class_weight="balanced",
            max_iter=1000,
            random_state=42
        )
    )

])


# --------------------------------------------------
# 7. TRAIN
# --------------------------------------------------

model.fit(X_train, y_train)

print("Model trained successfully.")


# --------------------------------------------------
# 8. TEST ON FUTURE TRANSACTIONS
# --------------------------------------------------

print("\n5. Testing model...")

fraud_probability = model.predict_proba(X_test)[:, 1]

predictions = (
    fraud_probability >= 0.50
).astype(int)


# --------------------------------------------------
# 9. RESULTS
# --------------------------------------------------

print("\nCLASSIFICATION REPORT")
print("-" * 60)

print(
    classification_report(
        y_test,
        predictions,
        digits=4
    )
)


print("\nCONFUSION MATRIX")
print("-" * 60)

print(
    confusion_matrix(
        y_test,
        predictions
    )
)


pr_auc = average_precision_score(
    y_test,
    fraud_probability
)

roc_auc = roc_auc_score(
    y_test,
    fraud_probability
)

print("\nMODEL SCORES")
print("-" * 60)

print(f"PR-AUC:  {pr_auc:.4f}")
print(f"ROC-AUC: {roc_auc:.4f}")


# --------------------------------------------------
# 10. SAVE MODEL
# --------------------------------------------------

os.makedirs(
    "models",
    exist_ok=True
)

joblib.dump(
    model,
    "models/baseline_fraud_model.joblib"
)

print(
    "\nModel saved to "
    "models/baseline_fraud_model.joblib"
)