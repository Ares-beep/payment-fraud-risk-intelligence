import duckdb

DATABASE = "data/fraud_risk.duckdb"

print("\nPAYMENT FRAUD PATTERN ANALYSIS")
print("=" * 70)

con = duckdb.connect(DATABASE)


# --------------------------------------------------
# 1. TRANSACTION AMOUNT
# --------------------------------------------------

print("\n1. TRANSACTION AMOUNT: FRAUD VS LEGITIMATE")
print("-" * 70)

amount_analysis = con.execute("""
SELECT
    is_fraud,
    COUNT(*) AS transactions,
    ROUND(AVG(amount), 2) AS average_amount,
    ROUND(MEDIAN(amount), 2) AS median_amount,
    ROUND(MIN(amount), 2) AS minimum_amount,
    ROUND(MAX(amount), 2) AS maximum_amount
FROM transactions_clean
WHERE amount IS NOT NULL
GROUP BY is_fraud
ORDER BY is_fraud
""").fetchdf()

print(amount_analysis)


# --------------------------------------------------
# 2. TRANSACTION ERRORS
# --------------------------------------------------

print("\n2. TRANSACTION ERRORS")
print("-" * 70)

error_analysis = con.execute("""
SELECT
    has_error,
    COUNT(*) AS transactions,
    SUM(is_fraud) AS fraud_transactions,
    ROUND(
        100.0 * SUM(is_fraud) / COUNT(*),
        4
    ) AS fraud_rate_pct
FROM transactions_clean
GROUP BY has_error
ORDER BY has_error
""").fetchdf()

print(error_analysis)


# --------------------------------------------------
# 3. FRAUD BY HOUR
# --------------------------------------------------

print("\n3. FRAUD BY TRANSACTION HOUR")
print("-" * 70)

hour_analysis = con.execute("""
SELECT
    transaction_hour,
    COUNT(*) AS transactions,
    SUM(is_fraud) AS fraud_transactions,
    ROUND(
        100.0 * SUM(is_fraud) / COUNT(*),
        4
    ) AS fraud_rate_pct
FROM transactions_clean
GROUP BY transaction_hour
ORDER BY transaction_hour
""").fetchdf()

print(hour_analysis)


# --------------------------------------------------
# 4. FRAUD BY DAY OF WEEK
# --------------------------------------------------

print("\n4. FRAUD BY DAY OF WEEK")
print("-" * 70)

day_analysis = con.execute("""
SELECT
    day_of_week,
    COUNT(*) AS transactions,
    SUM(is_fraud) AS fraud_transactions,
    ROUND(
        100.0 * SUM(is_fraud) / COUNT(*),
        4
    ) AS fraud_rate_pct
FROM transactions_clean
GROUP BY day_of_week
ORDER BY day_of_week
""").fetchdf()

print(day_analysis)


# --------------------------------------------------
# 5. HIGH-RISK MERCHANT CATEGORIES
# --------------------------------------------------

print("\n5. HIGH-RISK MERCHANT CATEGORIES")
print("-" * 70)

mcc_analysis = con.execute("""
SELECT
    mcc,
    COUNT(*) AS transactions,
    SUM(is_fraud) AS fraud_transactions,
    ROUND(
        100.0 * SUM(is_fraud) / COUNT(*),
        4
    ) AS fraud_rate_pct
FROM transactions_clean
GROUP BY mcc
HAVING COUNT(*) >= 10000
ORDER BY fraud_rate_pct DESC
LIMIT 15
""").fetchdf()

print(mcc_analysis)

con.close()