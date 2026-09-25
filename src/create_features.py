import duckdb

DATABASE = "data/fraud_risk.duckdb"
CARDS = "data/cards_data.csv"
USERS = "data/users_data.csv"

print("\nCREATING MACHINE LEARNING FEATURES")
print("=" * 60)

con = duckdb.connect(DATABASE)

con.execute("DROP TABLE IF EXISTS model_features_basic")

print("\n1. Building feature table...")

con.execute(f"""
CREATE TABLE model_features_basic AS

SELECT

    -- Keep transaction ID so we know which payment this is
    t.transaction_id,

    -- Original transaction amount
    t.amount,

    -- Refund / reversal indicator
    CASE
        WHEN t.amount < 0 THEN 1
        ELSE 0
    END AS is_refund,

    -- Use absolute amount for spending-size calculations
    ABS(t.amount) AS absolute_amount,


    -- PAYMENT METHOD
    CASE
        WHEN t.use_chip = 'Online Transaction'
        THEN 1 ELSE 0
    END AS is_online,

    CASE
        WHEN t.use_chip = 'Chip Transaction'
        THEN 1 ELSE 0
    END AS is_chip,

    CASE
        WHEN t.use_chip = 'Swipe Transaction'
        THEN 1 ELSE 0
    END AS is_swipe,


    -- TRANSACTION INFORMATION
    t.transaction_hour,
    t.day_of_week,
    t.has_error,

    -- Merchant category
    t.mcc,


    -- CARD INFORMATION
    c.has_chip,

    CASE
        WHEN c.card_on_dark_web = TRUE
        THEN 1 ELSE 0
    END AS card_on_dark_web,

    TRY_CAST(
        REPLACE(REPLACE(c.credit_limit, '$', ''), ',', '')
        AS DOUBLE
    ) AS credit_limit,


    -- How big is this payment compared with the card limit?
    CASE
        WHEN TRY_CAST(
            REPLACE(REPLACE(c.credit_limit, '$', ''), ',', '')
            AS DOUBLE
        ) > 0

        THEN ABS(t.amount) /
             TRY_CAST(
                REPLACE(REPLACE(c.credit_limit, '$', ''), ',', '')
                AS DOUBLE
             )

        ELSE NULL
    END AS amount_to_credit_limit,


    -- CUSTOMER INFORMATION
    u.credit_score,

    TRY_CAST(
        REPLACE(REPLACE(u.yearly_income, '$', ''), ',', '')
        AS DOUBLE
    ) AS yearly_income,

    TRY_CAST(
        REPLACE(REPLACE(u.total_debt, '$', ''), ',', '')
        AS DOUBLE
    ) AS total_debt,

    u.num_credit_cards,


    -- THE ANSWER WE WANT THE MODEL TO LEARN
    t.is_fraud

FROM transactions_clean t

LEFT JOIN read_csv_auto('{CARDS}') c
    ON t.card_id = c.id

LEFT JOIN read_csv_auto('{USERS}') u
    ON t.client_id = u.id
""")

print("Feature table created.")


print("\n2. Checking feature table")
print("-" * 60)

check = con.execute("""
SELECT
    COUNT(*) AS rows,
    SUM(is_fraud) AS fraud_transactions
FROM model_features_basic
""").fetchdf()

print(check)


print("\n3. Example ML data")
print("-" * 60)

sample = con.execute("""
SELECT
    transaction_id,
    amount,
    is_online,
    is_chip,
    is_swipe,
    has_error,
    card_on_dark_web,
    credit_limit,
    ROUND(amount_to_credit_limit, 3) AS amount_to_credit_limit,
    credit_score,
    yearly_income,
    is_fraud
FROM model_features_basic
LIMIT 10
""").fetchdf()

print(sample)

con.close()