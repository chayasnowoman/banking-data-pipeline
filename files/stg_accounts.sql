{{ config(materialized='ephemeral') }}

select
    account_id,
    customer_id,
    upper(trim(account_type)) as account_type,
    balance,
    upper(trim(currency)) as currency,
    upper(trim(status)) as account_status,
    cast(created_at as timestamp) as created_at
from {{ source('banking_raw', 'accounts') }}
