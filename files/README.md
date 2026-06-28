# Banking Data Pipeline

![Python](https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=white)
![AWS S3](https://img.shields.io/badge/AWS%20S3-569A31?logo=amazons3&logoColor=white)
![Snowflake](https://img.shields.io/badge/Snowflake-29B5E8?logo=snowflake&logoColor=white)
![dbt](https://img.shields.io/badge/dbt-FF694B?logo=dbt&logoColor=white)
![Apache Airflow](https://img.shields.io/badge/Apache%20Airflow-017CEE?logo=apacheairflow&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?logo=streamlit&logoColor=white)

---

## Overview

An end-to-end cloud-native data pipeline for a banking domain, covering data generation, cloud storage, warehouse ingestion, dimensional modeling, automated testing, change data capture (SCD Type 2), orchestration, analytics dashboard, and an AI-powered natural language query agent.

---

## Architecture

```
┌──────────────┐     ┌──────────────┐     ┌──────────────────────┐
│  Python/     │     │   AWS S3     │     │     Snowflake        │
│  Faker       ├────►│  (Parquet)   ├────►│     RAW schema       │
│  Generator   │     │              │     │  (Bronze layer)      │
└──────────────┘     └──────────────┘     └──────────┬───────────┘
                                                     │
                                          ┌──────────▼───────────┐
                                          │      dbt Cloud       │
                                          │                      │
                                          │  Staging (Silver)    │
                                          │  ┌─────────────────┐ │
                                          │  │ stg_customers   │ │
                                          │  │ stg_accounts    │ │
                                          │  │ stg_transactions│ │
                                          │  └────────┬────────┘ │
                                          │           │          │
                                          │  Marts (Gold)        │
                                          │  ┌─────────────────┐ │
                                          │  │ dim_customers   │ │
                                          │  │ dim_accounts    │ │
                                          │  │ fact_transactions│ │
                                          │  └─────────────────┘ │
                                          │                      │
                                          │  Snapshots (SCD2)    │
                                          │  ┌─────────────────┐ │
                                          │  │accounts_snapshot │ │
                                          │  └─────────────────┘ │
                                          │                      │
                                          │  Tests: 11 passing   │
                                          └──────────┬───────────┘
                                                     │
                              ┌───────────────────────┼──────────────────────┐
                              │                       │                      │
                   ┌──────────▼──────────┐ ┌─────────▼─────────┐ ┌─────────▼─────────┐
                   │   Airflow DAG      │ │  Streamlit        │ │  AI Agent         │
                   │   (Orchestration)  │ │  Dashboard        │ │  (NL → SQL)       │
                   │   4 tasks, daily   │ │  KPIs + Charts    │ │  Groq/Llama 3.3   │
                   └────────────────────┘ └───────────────────┘ └───────────────────┘
```

---

## Tech Stack

| Layer | Tool | Purpose |
|-------|------|---------|
| Data Generation | Python, Faker | Synthetic banking data (customers, accounts, transactions) |
| Cloud Storage | AWS S3 | Raw Parquet file storage |
| Data Warehouse | Snowflake | Cloud warehouse with Bronze/Silver/Gold layers |
| Transformation | dbt (Fusion) | Staging models, dimensional marts, tests, snapshots |
| Orchestration | Apache Airflow | Scheduled DAG with retries and task dependencies |
| Dashboard | Streamlit | KPI metrics, bar charts, trend lines |
| AI Agent | Groq (Llama 3.3), Streamlit | Natural language to SQL query interface |
| Infrastructure | AWS CLI, Docker, IAM | S3 access, Airflow containerization, role-based access |

---

## Data Model (Star Schema)

**Grain:** One row per transaction in `fact_transactions`

### Fact Table
- `fact_transactions` (5,000 rows, incremental materialization)
  - transaction_id, account_id, customer_id, transaction_type, amount, transaction_status, transaction_time
  - Incremental logic: only processes rows where `transaction_time > max(existing)`

### Dimension Tables
- `dim_customers` (500 rows) — customer details with full_name derivation
- `dim_accounts` (993 rows) — account type, balance, status

### Snapshot Table
- `accounts_snapshot` — SCD Type 2 tracking on balance and account_status
  - Strategy: `check` (compares column values each run)
  - Tracked columns: `balance`, `account_status`

---

## Data Quality Tests (11 total, all passing)

| Test Type | Model | Column | Purpose |
|-----------|-------|--------|---------|
| not_null | dim_customers | customer_id | No missing primary keys |
| unique | dim_customers | customer_id | No duplicate customers |
| not_null | dim_accounts | account_id | No missing primary keys |
| unique | dim_accounts | account_id | No duplicate accounts |
| not_null | dim_accounts | customer_id | Every account has an owner |
| relationships | dim_accounts | customer_id | FK integrity to dim_customers |
| accepted_values | dim_accounts | account_type | Only SAVINGS, CHECKING, FIXED_DEPOSIT |
| not_null | fact_transactions | transaction_id | No missing primary keys |
| unique | fact_transactions | transaction_id | No duplicate transactions |
| relationships | fact_transactions | account_id | FK integrity to dim_accounts |
| accepted_values | fact_transactions | transaction_type | Only DEPOSIT, WITHDRAWAL, TRANSFER, PAYMENT, REFUND |

---

## Pipeline Orchestration (Airflow)

DAG: `banking_data_pipeline` | Schedule: `@daily` | Retries: 2 | Retry delay: 5 min

```
check_s3_data → dbt_run → dbt_test → dbt_snapshot
```

- **check_s3_data** — Validates new data exists in S3
- **dbt_run** — Builds staging and mart models
- **dbt_test** — Runs all 11 data quality tests
- **dbt_snapshot** — Captures SCD Type 2 changes

Design decision: Tests run before snapshots so bad data never enters the historical record.

---

## Key Design Decisions

1. **Parquet over CSV for S3:** Columnar format with schema enforcement, 60% smaller file sizes, faster Snowflake ingestion via `MATCH_BY_COLUMN_NAME`.

2. **Ephemeral staging models:** Staging models don't create tables in Snowflake — they inject as CTEs into mart queries. Saves compute cost while keeping code modular.

3. **Incremental fact table:** `fact_transactions` uses `unique_key='transaction_id'` and `is_incremental()` to only process new rows. Critical for production where rebuilding millions of rows daily is wasteful.

4. **Check strategy for snapshots:** Used `check` over `timestamp` because the source table lacks a reliable `updated_at` column. Check compares actual column values each run.

5. **Separate dbt_test and dbt_snapshot tasks in Airflow:** If tests fail, snapshots are skipped — prevents bad data from entering SCD2 history.

6. **Star schema (Kimball):** Fact table at transaction grain with dimension tables for customers and accounts. Optimized for analytical queries ("total deposits by account type by month").

---

## Project Structure

```
banking-data-pipeline/
├── data-generator/
│   └── generate_banking_data.py      # Faker-based synthetic data generator
├── scripts/
│   └── upload_to_s3.py               # S3 upload script (boto3)
├── dbt_project/
│   ├── models/
│   │   ├── staging/
│   │   │   ├── stg_customers.sql     # Clean, trim, cast
│   │   │   ├── stg_accounts.sql
│   │   │   └── stg_transactions.sql
│   │   ├── marts/
│   │   │   ├── dim_customers.sql     # Customer dimension
│   │   │   ├── dim_accounts.sql      # Account dimension
│   │   │   └── fact_transactions.sql # Transaction fact (incremental)
│   │   ├── sources.yml
│   │   └── schema.yml                # 11 data quality tests
│   ├── snapshots/
│   │   └── accounts_snapshot.sql     # SCD Type 2
│   └── dbt_project.yml
├── airflow/
│   └── dags/
│       └── banking_dag.py            # 4-task daily DAG
├── dashboard.py                      # Streamlit analytics dashboard
├── ai_agent.py                       # Natural language SQL agent
└── README.md
```

---

## Dashboard Preview

**KPIs:** 500 customers | 993 accounts | 5,000 transactions | $9.2M total volume

**Visualizations:**
- Transaction count and volume by type (bar charts)
- Account distribution by type
- Top 10 customers by transaction volume
- Monthly transaction trend (line chart)

---

## AI Agent

Ask questions in plain English, get SQL + results:

**Example:** "Which customers had the most failed transactions?"

The agent:
1. Receives the question
2. LLM (Llama 3.3 via Groq) generates Snowflake SQL using schema context
3. Runs the query against the mart tables
4. Returns results in a table + auto-generated chart

---

## How to Run

### Prerequisites
- Python 3.10+
- AWS account with S3 access
- Snowflake account
- Docker (for Airflow)
- dbt Cloud account (free Developer plan)

### Steps

1. **Generate data:**
   ```bash
   cd data-generator && python generate_banking_data.py
   ```

2. **Upload to S3:**
   ```bash
   aws s3 cp customers.parquet s3://your-bucket/raw/
   aws s3 cp accounts.parquet s3://your-bucket/raw/
   aws s3 cp transactions.parquet s3://your-bucket/raw/
   ```

3. **Load into Snowflake:**
   ```sql
   COPY INTO BANKING_DB.RAW.customers FROM @banking_s3_stage/customers.parquet MATCH_BY_COLUMN_NAME = CASE_INSENSITIVE;
   ```

4. **Run dbt:**
   ```bash
   dbt run && dbt test && dbt snapshot
   ```

5. **Start Airflow:**
   ```bash
   docker start airflow-scheduler && docker start airflow-api-server
   ```

6. **Launch dashboard:**
   ```bash
   streamlit run dashboard.py
   ```

7. **Launch AI agent:**
   ```bash
   streamlit run ai_agent.py
   ```

---

## Author

**Chayanika Porel**
- LinkedIn: [Chayanika Porel](https://www.linkedin.com/in/chayanika-porel-ab9128176/)
- GitHub: [chayasnowoman](https://github.com/chayasnowoman)
