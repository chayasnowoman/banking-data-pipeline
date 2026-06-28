{{ config(materialized='table') }}

select
    account_id,
    customer_id,
    account_type,
    balance,
    currency,
    account_status,
    created_at,
    current_timestamp() as load_timestamp
from {{ ref('stg_accounts') }}
