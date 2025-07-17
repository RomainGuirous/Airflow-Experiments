from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime

default_args = {
    'owner': 'airflow_user',
    'depends_on_past': False,
    'retries': 1,
}

def my_task():
    print("Hello, Airflow!")

with DAG(
    dag_id='my_dag',
    default_args=default_args,
    description='Un DAG simple',
    schedule_interval='@daily',
    start_date=datetime(2025, 7, 10),
    catchup=False,
) as dag:

    task1 = PythonOperator(
        task_id='print_hello',
        python_callable=my_task,
    )