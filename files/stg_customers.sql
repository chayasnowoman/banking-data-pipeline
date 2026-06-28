{{ config(materialized='ephemeral') }}

select
    customer_id,
    trim(first_name) as first_name,
    trim(last_name) as last_name,
    lower(trim(email)) as email,
    phone,
    city,
    state,
    cast(created_at as timestamp) as created_at
from {{ source('banking_raw', 'customers') }}
