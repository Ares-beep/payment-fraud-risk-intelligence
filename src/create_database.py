import duckdb

DATABASE = "data/fraud_risk.duckdb"
TRANSACTIONS = "data/transactions_data.csv"
FRAUD_LABELS = "data/fraud_labels.csv"

print("\nCREATING PAYMENT FRAUD DATABASE")
print("=" * 60)

# Connect to our DuckDB database
con = duckdb.connect(DATABASE)

print("\n1. Creating clean labelled transaction table...")

con.execute("DROP TABLE IF EXISTS transactions_clean")

con.execute(f"""
CREATE TABLE transactions_clean AS

SELECT
    t.id AS transaction_id,

    t.date AS transaction_time,

    t.client_id,
    t.card_id,

    TRY_CAST(
        REPLACE(t.amount, '$', '')
        AS DOUBLE
    ) AS amount,

    t.use_chip,

    t.merchant_id,
    t.merchant_city,
    t.merchant_state,
    t.zip,
    t.mcc,
    t.errors,

    EXTRACT(HOUR FROM t.date) AS transaction_hour,

    EXTRACT(DOW FROM t.date) AS day_of_week,

    CASE
        WHEN t.errors IS NULL
             OR TRIM(t.errors) = ''
        THEN 0
        ELSE 1
    END AS has_error,

    f.is_fraud

FROM read_csv_auto(
    '{TRANSACTIONS}',
    quote='"',
    escape='"'
) AS t

INNER JOIN read_csv_auto(
    '{FRAUD_LABELS}'
) AS f

ON t.id = f.transaction_id
""")

print("Table created successfully.")


# --------------------------------------------------
# VERIFY DATABASE
# --------------------------------------------------

print("\n2. Database verification")
print("-" * 60)

result = con.execute("""
SELECT
    COUNT(*) AS transactions,
    SUM(is_fraud) AS fraud_transactions,
    ROUND(
        100.0 * SUM(is_fraud) / COUNT(*),
        4
    ) AS fraud_rate_pct
FROM transactions_clean
""").fetchall()

print(result)


# --------------------------------------------------
# CHECK AMOUNT CLEANING
# --------------------------------------------------

print("\n3. Example cleaned transactions")
print("-" * 60)

examples = con.execute("""
SELECT
    transaction_id,
    transaction_time,
    amount,
    use_chip,
    merchant_id,
    transaction_hour,
    day_of_week,
    has_error,
    is_fraud
FROM transactions_clean
LIMIT 10
""").fetchdf()

print(examples)


# --------------------------------------------------
# PAYMENT METHOD ANALYSIS
# --------------------------------------------------

print("\n4. Transaction method analysis")
print("-" * 60)

methods = con.execute("""
SELECT
    use_chip,
    COUNT(*) AS transactions,
    SUM(is_fraud) AS fraud_transactions,
    ROUND(
        100.0 * SUM(is_fraud) / COUNT(*),
        4
    ) AS fraud_rate_pct
FROM transactions_clean
GROUP BY use_chip
ORDER BY transactions DESC
""").fetchdf()

print(methods)

con.close()

print("\nDatabase saved to:")
print(DATABASE)