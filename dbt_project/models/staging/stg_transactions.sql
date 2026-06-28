{{ config(materialized='ephemeral') }}

select
    transaction_id,
    account_id,
    upper(trim(txn_type)) as transaction_type,
    amount,
    related_account_id,
    upper(trim(status)) as transaction_status,
    cast(created_at as timestamp) as transaction_time
from {{ source('banking_raw', 'transactions') }}
