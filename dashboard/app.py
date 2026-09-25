import streamlit as st
import duckdb
import json


with open("data/mcc_codes.json", "r") as file:
    mcc_data = json.load(file)

st.set_page_config(
    page_title="Payment Fraud Risk Intelligence",
    layout="wide"
)

st.title("💳 Payment Fraud Risk Intelligence")
st.write("Payment transaction monitoring and fraud analysis dashboard")

# Connect to our database
con = duckdb.connect("data/fraud_risk.duckdb", read_only=True)

# Main numbers
summary = con.execute("""
SELECT
    COUNT(*) AS total_transactions,
    SUM(is_fraud) AS fraud_transactions,
    ROUND(
        100.0 * SUM(is_fraud) / COUNT(*),
        4
    ) AS fraud_rate
FROM transactions_clean
""").fetchone()

total_transactions = summary[0]
fraud_transactions = summary[1]
fraud_rate = summary[2]

# Display numbers
col1, col2, col3 = st.columns(3)

col1.metric(
    "Transactions Analysed",
    f"{total_transactions:,}"
)

col2.metric(
    "Fraud Transactions",
    f"{int(fraud_transactions):,}"
)

col3.metric(
    "Fraud Rate",
    f"{fraud_rate}%"
)

st.divider()

# --------------------------------------------------
# FRAUD BY PAYMENT METHOD
# --------------------------------------------------

st.subheader("Fraud Risk by Payment Method")

payment_methods = con.execute("""
SELECT
    CASE
        WHEN use_chip = 'Online Transaction' THEN 'Online'
        WHEN use_chip = 'Chip Transaction' THEN 'Chip'
        WHEN use_chip = 'Swipe Transaction' THEN 'Swipe'
        ELSE use_chip
    END AS payment_method,

    ROUND(
        100.0 * SUM(is_fraud) / COUNT(*),
        4
    ) AS fraud_rate_percent

FROM transactions_clean

GROUP BY use_chip

ORDER BY fraud_rate_percent DESC
""").fetchdf()

st.bar_chart(
    payment_methods,
    x="payment_method",
    y="fraud_rate_percent"
)

st.caption(
    "Percentage of transactions identified as fraud for each payment method."
)


# --------------------------------------------------
# FRAUD RATE OVER TIME
# --------------------------------------------------

st.divider()

st.subheader("Fraud Rate Over Time")

fraud_over_time = con.execute("""
SELECT
    DATE_TRUNC('month', transaction_time) AS month,

    ROUND(
        100.0 * SUM(is_fraud) / COUNT(*),
        4
    ) AS fraud_rate_percent

FROM transactions_clean

GROUP BY month

ORDER BY month
""").fetchdf()

st.line_chart(
    fraud_over_time,
    x="month",
    y="fraud_rate_percent"
)

st.caption(
    "Monthly fraud rate showing how fraud patterns changed over time."
)


# --------------------------------------------------
# HIGH-RISK MERCHANT CATEGORIES
# --------------------------------------------------

st.divider()

st.subheader("High-Risk Merchant Categories")

merchant_risk = con.execute("""
SELECT
    mcc,
    COUNT(*) AS transactions,
    SUM(is_fraud) AS fraud_transactions,

    ROUND(
        100.0 * SUM(is_fraud) / COUNT(*),
        4
    ) AS fraud_rate_percent

FROM transactions_clean

GROUP BY mcc

HAVING COUNT(*) >= 10000

ORDER BY fraud_rate_percent DESC

LIMIT 10
""").fetchdf()
merchant_risk["merchant_category"] = (
    merchant_risk["mcc"]
    .astype(str)
    .map(mcc_data)
)

st.dataframe(
    merchant_risk,
    use_container_width=True,
    hide_index=True
)

st.caption(
    "Merchant categories with at least 10,000 transactions, "
    "ranked by fraud rate."
)

# --------------------------------------------------
# TRANSACTION INVESTIGATOR
# --------------------------------------------------

st.divider()

st.subheader("🔎 Transaction Investigator")

st.write(
    "Enter a transaction ID to inspect the payment and its behavioural information."
)

transaction_id = st.number_input(
    "Transaction ID",
    min_value=1,
    step=1
)

if st.button("Analyse Transaction"):

    transaction = con.execute("""
    SELECT

        t.transaction_id,
        t.transaction_time,
        t.amount,
        t.use_chip,
        t.merchant_id,
        t.mcc,
        t.has_error,
        t.is_fraud,

        ROUND(h.customer_previous_avg, 2) AS customer_avg_spend,
        ROUND(h.card_previous_avg, 2) AS card_avg_spend,

        ROUND(
            h.amount_vs_customer_avg,
            2
        ) AS amount_vs_customer_avg,

        ROUND(
            h.amount_vs_card_avg,
            2
        ) AS amount_vs_card_avg

    FROM transactions_clean t

    LEFT JOIN behavior_features h
        ON t.transaction_id = h.transaction_id

    WHERE t.transaction_id = ?

    LIMIT 1
    """, [transaction_id]).fetchdf()


    if len(transaction) == 0:

        st.warning("Transaction not found.")

    else:

        row = transaction.iloc[0]

        st.success("Transaction found.")

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "Amount",
            f"${row['amount']:,.2f}"
        )

        col2.metric(
            "Payment Method",
            row["use_chip"]
        )

        col3.metric(
            "Merchant Category",
            str(row["mcc"])
        )


        st.write("### Behaviour Information")

        col1, col2 = st.columns(2)

        col1.write(
            f"**Customer previous average:** "
            f"${row['customer_avg_spend']:,.2f}"
        )

        col2.write(
            f"**Card previous average:** "
            f"${row['card_avg_spend']:,.2f}"
        )


        col1, col2 = st.columns(2)

        col1.write(
            f"**Compared with customer average:** "
            f"{row['amount_vs_customer_avg']:.2f}×"
        )

        col2.write(
            f"**Compared with card average:** "
            f"{row['amount_vs_card_avg']:.2f}×"
        )


        if row["has_error"] == 1:
            st.warning("⚠️ This transaction had an error.")


        if row["is_fraud"] == 1:
            st.error("Dataset label: FRAUD")
        else:
            st.success("Dataset label: LEGITIMATE")
con.close()