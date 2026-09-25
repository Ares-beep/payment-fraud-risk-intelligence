import duckdb
import json

USERS = "data/users_data.csv"
CARDS = "data/cards_data.csv"
MCC = "data/mcc_codes.json"

print("\nCUSTOMER, CARD & MERCHANT DATA INSPECTION")
print("=" * 70)

# USERS
print("\n1. USERS TABLE COLUMNS")
print("-" * 70)

users_schema = duckdb.sql(f"""
DESCRIBE
SELECT *
FROM read_csv_auto('{USERS}')
""")

print(users_schema)

print("\nExample users:")
print(
    duckdb.sql(f"""
    SELECT *
    FROM read_csv_auto('{USERS}')
    LIMIT 5
    """)
)

# CARDS
print("\n2. CARDS TABLE COLUMNS")
print("-" * 70)

cards_schema = duckdb.sql(f"""
DESCRIBE
SELECT *
FROM read_csv_auto('{CARDS}')
""")

print(cards_schema)

print("\nExample cards:")
print(
    duckdb.sql(f"""
    SELECT *
    FROM read_csv_auto('{CARDS}')
    LIMIT 5
    """)
)

# MCC CODES
print("\n3. MERCHANT CATEGORY DATA")
print("-" * 70)

with open(MCC, "r") as file:
    mcc_data = json.load(file)

print("Number of merchant categories:", len(mcc_data))

print("\nExample MCC codes:")
for code, description in list(mcc_data.items())[:10]:
    print(code, "->", description)