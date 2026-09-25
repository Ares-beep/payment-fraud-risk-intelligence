import duckdb

DATABASE = "data/fraud_risk.duckdb"
CARDS = "data/cards_data.csv"
USERS = "data/users_data.csv"

print("\nCHECKING DATA RELATIONSHIPS")
print("=" * 60)

con = duckdb.connect(DATABASE)

result = con.execute(f"""
SELECT

    COUNT(*) AS total_transactions,

    COUNT(c.id) AS card_matches,

    COUNT(u.id) AS customer_matches

FROM transactions_clean t

LEFT JOIN read_csv_auto('{CARDS}') c
    ON t.card_id = c.id

LEFT JOIN read_csv_auto('{USERS}') u
    ON t.client_id = u.id
""").fetchdf()

print("\n1. JOIN CHECK")
print(result)


print("\n2. EXAMPLE CONNECTED TRANSACTIONS")
print("-" * 60)

examples = con.execute(f"""
SELECT

    t.transaction_id,
    t.amount,
    t.use_chip,

    t.client_id,

    c.id AS card_id,
    c.card_brand,
    c.card_type,
    c.credit_limit,
    c.has_chip,
    c.card_on_dark_web,

    u.credit_score,
    u.yearly_income

FROM transactions_clean t

LEFT JOIN read_csv_auto('{CARDS}') c
    ON t.card_id = c.id

LEFT JOIN read_csv_auto('{USERS}') u
    ON t.client_id = u.id

LIMIT 10
""").fetchdf()

print(examples)

con.close()