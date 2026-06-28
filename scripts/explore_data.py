import pandas as pd

customers = pd.read_parquet('customers.parquet')
accounts = pd.read_parquet('accounts.parquet')
transactions = pd.read_parquet('transactions.parquet')

print("=== CUSTOMERS ===")
print(f"Rows: {len(customers)}")
print(customers.dtypes)
print(customers.head())

print("\n=== ACCOUNTS ===")
print(f"Rows: {len(accounts)}")
print(accounts.dtypes)
print(accounts.head())

print("\n=== TRANSACTIONS ===")
print(f"Rows: {len(transactions)}")
print(transactions.dtypes)
print(transactions.head())