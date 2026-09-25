import duckdb

DATABASE = "data/fraud_risk.duckdb"

print("\nCHECKING TRAIN VS TEST FRAUD PATTERNS")
print("=" * 65)

con = duckdb.connect(DATABASE)

cutoff = con.execute("""
SELECT quantile_cont(transaction_time, 0.80)
FROM transactions_clean
""").fetchone()[0]

print("\nTime split:")
print(cutoff)


print("\n1. OVERALL FRAUD RATE")
print("-" * 65)

print(
    con.execute("""
    SELECT

        CASE
            WHEN transaction_time < ?
            THEN 'TRAIN - Past'
            ELSE 'TEST - Future'
        END AS dataset,

        COUNT(*) AS transactions,

        SUM(is_fraud) AS fraud,

        ROUND(
            100.0 * SUM(is_fraud) / COUNT(*),
            4
        ) AS fraud_rate_pct

    FROM transactions_clean

    GROUP BY dataset
    """, [cutoff]).fetchdf()
)


print("\n2. ONLINE TRANSACTION FRAUD")
print("-" * 65)

print(
    con.execute("""
    SELECT

        CASE
            WHEN transaction_time < ?
            THEN 'TRAIN - Past'
            ELSE 'TEST - Future'
        END AS dataset,

        use_chip,

        COUNT(*) AS transactions,

        SUM(is_fraud) AS fraud,

        ROUND(
            100.0 * SUM(is_fraud) / COUNT(*),
            4
        ) AS fraud_rate_pct

    FROM transactions_clean

    GROUP BY
        dataset,
        use_chip

    ORDER BY
        dataset,
        fraud_rate_pct DESC
    """, [cutoff]).fetchdf()
)


print("\n3. FRAUD AMOUNT")
print("-" * 65)

print(
    con.execute("""
    SELECT

        CASE
            WHEN transaction_time < ?
            THEN 'TRAIN - Past'
            ELSE 'TEST - Future'
        END AS dataset,

        is_fraud,

        ROUND(AVG(ABS(amount)), 2) AS avg_amount,

        ROUND(MEDIAN(ABS(amount)), 2) AS median_amount

    FROM transactions_clean

    GROUP BY
        dataset,
        is_fraud

    ORDER BY
        dataset,
        is_fraud
    """, [cutoff]).fetchdf()
)

con.close()