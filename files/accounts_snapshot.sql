{% snapshot accounts_snapshot %}
{{
    config(
        target_schema='DBT_CPOREL',
        target_database='BANKING_DB',
        unique_key='account_id',
        strategy='check',
        check_cols=['balance', 'account_status']
    )
}}

select
    account_id,
    customer_id,
    account_type,
    balance,
    upper(trim(status)) as account_status,
    currency,
    created_at
from {{ source('banking_raw', 'accounts') }}

{% endsnapshot %}
