"""
Banking Data Generator
Generates synthetic banking data (customers, accounts, transactions)
and saves as both CSV and Parquet for the cloud-native pipeline project.
"""

import pandas as pd
import numpy as np
from faker import Faker
from datetime import datetime, timedelta
import random
import os

fake = Faker()
Faker.seed(42)
random.seed(42)
np.random.seed(42)

# === Configuration ===
NUM_CUSTOMERS = 500
ACCOUNTS_PER_CUSTOMER_RANGE = (1, 3)  # 1 to 3 accounts per customer
NUM_TRANSACTIONS = 5000
OUTPUT_DIR = "/home/claude/banking-data"

os.makedirs(f"{OUTPUT_DIR}/csv", exist_ok=True)
os.makedirs(f"{OUTPUT_DIR}/parquet", exist_ok=True)

# === 1. Generate Customers ===
print("Generating customers...")
customers = []
for i in range(1, NUM_CUSTOMERS + 1):
    customers.append({
        "customer_id": i,
        "first_name": fake.first_name(),
        "last_name": fake.last_name(),
        "email": fake.unique.email(),
        "phone": fake.phone_number(),
        "city": fake.city(),
        "state": fake.state_abbr(),
        "created_at": fake.date_time_between(
            start_date=datetime(2020, 1, 1),
            end_date=datetime(2024, 12, 31)
        ).strftime("%Y-%m-%d %H:%M:%S")
    })

df_customers = pd.DataFrame(customers)
print(f"  ✅ {len(df_customers)} customers generated")

# === 2. Generate Accounts ===
print("Generating accounts...")
accounts = []
account_id = 1
account_types = ["SAVINGS", "CHECKING", "FIXED_DEPOSIT"]

for cust in customers:
    num_accounts = random.randint(*ACCOUNTS_PER_CUSTOMER_RANGE)
    for _ in range(num_accounts):
        acct_type = random.choice(account_types)
        balance = round(random.uniform(100, 50000), 2)
        
        # Account created after customer created
        cust_date = datetime.strptime(cust["created_at"], "%Y-%m-%d %H:%M:%S")
        acct_date = cust_date + timedelta(days=random.randint(0, 30))
        
        accounts.append({
            "account_id": account_id,
            "customer_id": cust["customer_id"],
            "account_type": acct_type,
            "balance": balance,
            "currency": "USD",
            "status": random.choices(
                ["ACTIVE", "INACTIVE", "CLOSED"],
                weights=[85, 10, 5]
            )[0],
            "created_at": acct_date.strftime("%Y-%m-%d %H:%M:%S")
        })
        account_id += 1

df_accounts = pd.DataFrame(accounts)
print(f"  ✅ {len(df_accounts)} accounts generated")

# === 3. Generate Transactions ===
print("Generating transactions...")
transactions = []
active_account_ids = [a["account_id"] for a in accounts if a["status"] == "ACTIVE"]
all_account_ids = [a["account_id"] for a in accounts]

txn_types = ["DEPOSIT", "WITHDRAWAL", "TRANSFER", "PAYMENT", "REFUND"]
statuses = ["COMPLETED", "PENDING", "FAILED"]

for i in range(1, NUM_TRANSACTIONS + 1):
    acct_id = random.choice(active_account_ids)
    txn_type = random.choices(
        txn_types,
        weights=[30, 25, 20, 20, 5]
    )[0]
    
    # Amount varies by transaction type
    if txn_type in ["DEPOSIT", "TRANSFER"]:
        amount = round(random.uniform(50, 5000), 2)
    elif txn_type == "PAYMENT":
        amount = round(random.uniform(10, 2000), 2)
    elif txn_type == "REFUND":
        amount = round(random.uniform(5, 500), 2)
    else:
        amount = round(random.uniform(20, 3000), 2)
    
    related_account = None
    if txn_type == "TRANSFER":
        candidates = [a for a in active_account_ids if a != acct_id]
        if candidates:
            related_account = random.choice(candidates)
    
    status = random.choices(statuses, weights=[90, 7, 3])[0]
    
    # Transaction date: random within last 2 years
    txn_date = fake.date_time_between(
        start_date=datetime(2023, 1, 1),
        end_date=datetime(2025, 6, 15)
    )
    
    transactions.append({
        "transaction_id": i,
        "account_id": acct_id,
        "txn_type": txn_type,
        "amount": amount,
        "related_account_id": related_account,
        "status": status,
        "created_at": txn_date.strftime("%Y-%m-%d %H:%M:%S")
    })

df_transactions = pd.DataFrame(transactions)
print(f"  ✅ {len(df_transactions)} transactions generated")

# === Save as CSV ===
print("\nSaving CSVs...")
df_customers.to_csv(f"{OUTPUT_DIR}/csv/customers.csv", index=False)
df_accounts.to_csv(f"{OUTPUT_DIR}/csv/accounts.csv", index=False)
df_transactions.to_csv(f"{OUTPUT_DIR}/csv/transactions.csv", index=False)
print("  ✅ CSVs saved")

# === Save as Parquet ===
print("Saving Parquet files...")
df_customers.to_parquet(f"{OUTPUT_DIR}/parquet/customers.parquet", index=False)
df_accounts.to_parquet(f"{OUTPUT_DIR}/parquet/accounts.parquet", index=False)
df_transactions.to_parquet(f"{OUTPUT_DIR}/parquet/transactions.parquet", index=False)
print("  ✅ Parquet files saved")

# === Summary ===
print("\n" + "="*50)
print("DATA GENERATION SUMMARY")
print("="*50)
print(f"Customers:    {len(df_customers):>6} rows")
print(f"Accounts:     {len(df_accounts):>6} rows")
print(f"Transactions: {len(df_transactions):>6} rows")
print(f"\nAccount types: {df_accounts['account_type'].value_counts().to_dict()}")
print(f"Account status: {df_accounts['status'].value_counts().to_dict()}")
print(f"Txn types: {df_transactions['txn_type'].value_counts().to_dict()}")
print(f"Txn status: {df_transactions['status'].value_counts().to_dict()}")
print(f"\nFiles saved to: {OUTPUT_DIR}/")
