import streamlit as st
import snowflake.connector
import pandas as pd
import os

# Snowflake connection
@st.cache_resource
def get_connection():
    return snowflake.connector.connect(
        user=os.getenv('SNOWFLAKE_USER', 'SNOWUSER2'),
        password=os.getenv('SNOWFLAKE_PASSWORD'),
        account=os.getenv('SNOWFLAKE_ACCOUNT', 'mjkfile-dgb10852'),
        warehouse='COMPUTE_WH',
        database='BANKING_DB',
        schema='DBT_CPOREL'
    )

def run_query(query):
    conn = get_connection()
    return pd.read_sql(query, conn)

st.set_page_config(page_title="Banking Analytics", layout="wide")
st.title("Banking Data Pipeline Dashboard")

col1, col2, col3, col4 = st.columns(4)

customers = run_query("SELECT COUNT(*) as cnt FROM dim_customers")
accounts = run_query("SELECT COUNT(*) as cnt FROM dim_accounts")
transactions = run_query("SELECT COUNT(*) as cnt FROM fact_transactions")
total_volume = run_query("SELECT ROUND(SUM(amount), 2) as total FROM fact_transactions")

col1.metric("Total Customers", f"{customers['CNT'][0]:,}")
col2.metric("Total Accounts", f"{accounts['CNT'][0]:,}")
col3.metric("Total Transactions", f"{transactions['CNT'][0]:,}")
col4.metric("Transaction Volume", f"${total_volume['TOTAL'][0]:,.2f}")

st.divider()

st.subheader("Transactions by Type")
txn_by_type = run_query("""
    SELECT transaction_type, COUNT(*) as count, ROUND(SUM(amount), 2) as total_amount
    FROM fact_transactions
    GROUP BY transaction_type
    ORDER BY count DESC
""")
col1, col2 = st.columns(2)
col1.bar_chart(txn_by_type.set_index('TRANSACTION_TYPE')['COUNT'])
col2.bar_chart(txn_by_type.set_index('TRANSACTION_TYPE')['TOTAL_AMOUNT'])

st.subheader("Accounts by Type")
acct_by_type = run_query("""
    SELECT account_type, COUNT(*) as count
    FROM dim_accounts
    GROUP BY account_type
""")
st.bar_chart(acct_by_type.set_index('ACCOUNT_TYPE')['COUNT'])

st.subheader("Top 10 Customers by Transaction Volume")
top_customers = run_query("""
    SELECT c.full_name, COUNT(f.transaction_id) as txn_count,
           ROUND(SUM(f.amount), 2) as total_amount
    FROM fact_transactions f
    JOIN dim_customers c ON f.customer_id = c.customer_id
    GROUP BY c.full_name
    ORDER BY total_amount DESC
    LIMIT 10
""")
st.dataframe(top_customers, use_container_width=True)

st.subheader("Monthly Transaction Trend")
monthly = run_query("""
    SELECT DATE_TRUNC('month', transaction_time) as month,
           COUNT(*) as txn_count,
           ROUND(SUM(amount), 2) as total_amount
    FROM fact_transactions
    GROUP BY month
    ORDER BY month
""")
st.line_chart(monthly.set_index('MONTH')['TOTAL_AMOUNT'])