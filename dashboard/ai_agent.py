import streamlit as st
import snowflake.connector
import pandas as pd
from groq import Groq
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
    try:
        return pd.read_sql(query, conn)
    except Exception as e:
        return str(e)

SCHEMA_CONTEXT = """
You are a SQL expert. Generate Snowflake SQL queries based on user questions.

Available tables in BANKING_DB.DBT_CPOREL:

1. dim_customers (500 rows):
   - customer_id (INT, PK)
   - first_name, last_name, full_name (VARCHAR)
   - email, phone, city, state (VARCHAR)
   - created_at (TIMESTAMP)

2. dim_accounts (993 rows):
   - account_id (INT, PK)
   - customer_id (INT, FK to dim_customers)
   - account_type (VARCHAR: SAVINGS, CHECKING, FIXED_DEPOSIT)
   - balance (NUMERIC)
   - currency (VARCHAR)
   - account_status (VARCHAR: ACTIVE, INACTIVE, CLOSED)
   - created_at (TIMESTAMP)

3. fact_transactions (5000 rows):
   - transaction_id (INT, PK)
   - account_id (INT, FK to dim_accounts)
   - customer_id (INT, FK to dim_customers)
   - transaction_type (VARCHAR: DEPOSIT, WITHDRAWAL, TRANSFER, PAYMENT, REFUND)
   - amount (NUMERIC)
   - related_account_id (INT, nullable)
   - transaction_status (VARCHAR: COMPLETED, PENDING, FAILED)
   - transaction_time (TIMESTAMP)

Rules:
- Return ONLY the SQL query, no explanation
- Use fully qualified table names: BANKING_DB.DBT_CPOREL.table_name
- Always use uppercase for table and column names in Snowflake
- LIMIT results to 20 rows unless user asks for more
"""

def ask_llm(question):
    client = Groq(api_key=os.getenv('GROQ_API_KEY'))
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": SCHEMA_CONTEXT},
            {"role": "user", "content": question}
        ],
        max_tokens=500,
        temperature=0,
    )
    sql = response.choices[0].message.content.strip()
    sql = sql.replace("```sql", "").replace("```", "").strip()
    return sql

st.set_page_config(page_title="Banking AI Agent", layout="wide")
st.title("Banking Data AI Agent")
st.caption("Ask questions about your banking data in plain English")

with st.expander("Example questions"):
    st.markdown("""
    - Which customers had the most failed transactions?
    - What is the average balance by account type?
    - Show me the top 5 cities by transaction volume
    - How many transactions happened each month in 2024?
    - Which accounts have a balance over $40,000?
    """)

question = st.text_input("Ask a question about your banking data:")

if question:
    with st.spinner("Generating SQL..."):
        sql = ask_llm(question)

    st.subheader("Generated SQL")
    st.code(sql, language="sql")

    with st.spinner("Running query..."):
        result = run_query(sql)

    st.subheader("Results")
    if isinstance(result, str):
        st.error(f"Query error: {result}")
    else:
        st.dataframe(result, use_container_width=True)
        if len(result) > 0 and len(result.columns) >= 2:
            try:
                st.bar_chart(result.set_index(result.columns[0])[result.columns[1]])
            except:
                pass