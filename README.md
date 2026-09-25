# Payment Fraud Risk Intelligence System

A financial fraud analysis and machine-learning project built using Python, SQL, DuckDB, Scikit-learn and Streamlit.

The project analyses millions of card transactions to explore fraud patterns and build a prototype fraud-detection model.

## Project Overview

The dataset contains 8,914,963 labelled transactions together with customer, card and merchant information.

The main goal was to explore:

- What patterns are associated with fraudulent payments?
- Can customer spending behaviour help identify unusual transactions?
- How well can a machine-learning model identify fraud?
- Do fraud patterns change over time?

## Dataset

The labelled data contains:

- 8,914,963 transactions
- 8,901,631 legitimate transactions
- 13,332 fraudulent transactions
- Fraud rate: 0.1495%

The raw dataset is not included in this repository because of its size.

## Technologies Used

- Python
- SQL
- DuckDB
- Pandas
- Scikit-learn
- Streamlit

## Project Process

The project follows this general process:

Raw transaction data  
→ Data cleaning  
→ Join fraud labels  
→ Add customer and card information  
→ Analyse fraud patterns  
→ Create behavioural features  
→ Train machine-learning models  
→ Visualise results using Streamlit

## Fraud Analysis

Some of the areas investigated included:

- Fraud rate by payment method
- Transaction amount
- Transaction errors
- Transaction time
- Merchant category
- Customer spending behaviour
- Card spending behaviour

One useful finding was that fraudulent transactions were often larger compared with a customer's previous average spending.

## Feature Engineering

Features used in the project included:

- Transaction amount
- Online / chip / swipe transaction
- Transaction hour
- Day of week
- Transaction errors
- Card credit limit
- Credit score
- Transaction amount compared with card limit
- Customer previous average spending
- Card previous average spending
- Transaction amount compared with normal customer spending

Historical spending features were calculated using previous transactions rather than future transactions.

## Machine Learning

I first trained a simple baseline classification model.

The first model performed poorly when tested on newer transactions.

Further analysis showed that the fraud behaviour had changed significantly over time.

For example, online transactions had a much higher fraud rate in the older data, while chip transactions became more prominent in the newer period.

A second gradient-boosting model was then tested using more recent transaction data.

Because fraud represents less than 0.2% of transactions, accuracy alone was not considered a useful measure of performance.

The project also considered:

- Precision
- Recall
- F1-score
- PR-AUC
- ROC-AUC

## Dashboard

A Streamlit dashboard was created to visualise:

- Total transactions analysed
- Total fraudulent transactions
- Overall fraud rate
- Fraud rate by payment method
- Fraud rate over time
- High-risk merchant categories

## What I Learned

This project helped me gain practical experience with:

- Working with large datasets
- SQL joins and aggregation
- DuckDB
- Data cleaning
- Feature engineering
- Imbalanced machine-learning datasets
- Model evaluation
- Data drift
- Streamlit dashboards

## Project Status

This is a learning and portfolio project.

It is a prototype and is not intended to represent a production banking or payment-processing system.