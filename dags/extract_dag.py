from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import pandas as pd


def extract_csv():
    # Chemin du fichier CSV
    file_path = "/opt/airflow/dags/imdb_1000.csv"
    # Lire le fichier CSV
    df = pd.read_csv(file_path)
    print(df.head())  # Affiche les premières lignes pour vérifier
    return df.to_dict()  # Retourne les données sous forme de dictionnaire


def log_data(**context):
    # Récupère les données extraites depuis le contexte
    extracted_data = context["task_instance"].xcom_pull(task_ids="extract_csv")
    print("Données extraites :")
    print(extracted_data)


default_args = {
    "owner": "airflow_user",
    # if True, une tâche dépendante de la tâche précédente
    "depends_on_past": False,
    # Nombre de tentatives en cas d'échec
    "retries": 1,
}

with DAG(
    dag_id="etl_movies_dag",
    default_args=default_args,
    description="ETL pour les films IMDb",
    schedule_interval="*/1 * * * *",  # Exécution toutes les minutes
    start_date=datetime(2025, 7, 16),
    catchup=False,
) as dag:
    extract_task = PythonOperator(
        task_id="extract_csv",
        python_callable=extract_csv,
    )

    log_task = PythonOperator(
        task_id="log_data",
        python_callable=log_data,
        provide_context=True,
    )

    extract_task >> log_task  # Définir l'ordre des tâches
