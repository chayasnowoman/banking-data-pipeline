{{ config(materialized='table') }}

select
    customer_id,
    trim(first_name) as first_name,
    trim(last_name) as last_name,
    trim(first_name) || ' ' || trim(last_name) as full_name,
    lower(trim(email)) as email,
    phone,
    city,
    state,
    cast(created_at as timestamp) as created_at,
    current_timestamp() as load_timestamp
from {{ source('banking_raw', 'customers') }}
