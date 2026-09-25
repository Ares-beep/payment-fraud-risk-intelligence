import duckdb

DATABASE = "data/fraud_risk.duckdb"

print("\nCREATING BEHAVIOURAL FRAUD FEATURES")
print("=" * 60)

con = duckdb.connect(DATABASE)

con.execute("DROP TABLE IF EXISTS behavior_features")

print("\n1. Calculating normal customer/card spending...")

con.execute("""
CREATE TABLE behavior_features AS

WITH spending_history AS (

    SELECT

        t.transaction_id,

        b.absolute_amount,

        AVG(b.absolute_amount) OVER (
            PARTITION BY t.client_id
            ORDER BY t.transaction_time, t.transaction_id
            ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING
        ) AS customer_previous_avg,

        AVG(b.absolute_amount) OVER (
            PARTITION BY t.card_id
            ORDER BY t.transaction_time, t.transaction_id
            ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING
        ) AS card_previous_avg

    FROM transactions_clean t

    INNER JOIN model_features_basic b
        ON t.transaction_id = b.transaction_id
)

SELECT

    transaction_id,

    customer_previous_avg,

    card_previous_avg,

    CASE
        WHEN customer_previous_avg > 0
        THEN absolute_amount / customer_previous_avg
        ELSE NULL
    END AS amount_vs_customer_avg,

    CASE
        WHEN card_previous_avg > 0
        THEN absolute_amount / card_previous_avg
        ELSE NULL
    END AS amount_vs_card_avg

FROM spending_history
""")

print("Behaviour features created.")


print("\n2. NUMBER OF BEHAVIOUR FEATURES")
print("-" * 60)

print(
    con.execute("""
    SELECT COUNT(*) AS rows
    FROM behavior_features
    """).fetchdf()
)


print("\n3. EXAMPLE BEHAVIOUR FEATURES")
print("-" * 60)

print(
    con.execute("""
    SELECT
        transaction_id,
        ROUND(customer_previous_avg, 2) AS customer_previous_avg,
        ROUND(card_previous_avg, 2) AS card_previous_avg,
        ROUND(amount_vs_customer_avg, 2) AS amount_vs_customer_avg,
        ROUND(amount_vs_card_avg, 2) AS amount_vs_card_avg
    FROM behavior_features
    WHERE customer_previous_avg IS NOT NULL
    LIMIT 10
    """).fetchdf()
)


print("\n4. FRAUD VS NORMAL BEHAVIOUR")
print("-" * 60)

print(
    con.execute("""
    SELECT

        b.is_fraud,

        ROUND(
            MEDIAN(f.amount_vs_customer_avg),
            2
        ) AS median_vs_customer_avg,

        ROUND(
            MEDIAN(f.amount_vs_card_avg),
            2
        ) AS median_vs_card_avg

    FROM model_features_basic b

    INNER JOIN behavior_features f
        ON b.transaction_id = f.transaction_id

    WHERE
        f.amount_vs_customer_avg IS NOT NULL
        AND f.amount_vs_card_avg IS NOT NULL

    GROUP BY b.is_fraud

    ORDER BY b.is_fraud
    """).fetchdf()
)

con.close()

print("\nDone.")