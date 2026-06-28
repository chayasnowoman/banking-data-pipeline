
from airflow import DAG
from airflow.providers.standard.operators.bash import BashOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'chayanika',
    'depends_on_past': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    dag_id='banking_data_pipeline',
    default_args=default_args,
    description='Banking pipeline: dbt run, test, snapshot',
    schedule='@daily',
    start_date=datetime(2026, 6, 1),
    catchup=False,
    tags=['banking', 'dbt'],
) as dag:

    check_data = BashOperator(
        task_id='check_s3_data',
        bash_command='echo Checking S3 for new files',
    )

    dbt_run = BashOperator(
        task_id='dbt_run',
        bash_command='echo Running dbt models',
    )

    dbt_test = BashOperator(
        task_id='dbt_test',
        bash_command='echo Running dbt tests',
    )

    dbt_snapshot = BashOperator(
        task_id='dbt_snapshot',
        bash_command='echo Running dbt snapshots',
    )

    check_data >> dbt_run >> dbt_test >> dbt_snapshot
