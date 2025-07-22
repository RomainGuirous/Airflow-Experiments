from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import pandas as pd


def extract_to_df(**context):
    # Chemin du fichier CSV
    file_path = "/opt/airflow/dags/imdb_1000.csv"
    # Lire le fichier CSV
    df = pd.read_csv(file_path)

    # Récupérer l'offset depuis XComs (par défaut 0)
    offset = (
        context["task_instance"].xcom_pull(task_ids="extract_to_df", key="offset") or 0
    )

    # Vérifier si l'offset dépasse la taille du fichier
    if offset >= len(df):
        print("Toutes les lignes ont été traitées.")
        return None  # Arrêter l'extraction

    # Calculer le nombre de lignes restantes
    remaining_rows = len(df) - offset

    # Extraire les lignes restantes ou un maximum de 50 lignes
    batch_size = min(50, remaining_rows)
    batch = df.iloc[offset : offset + batch_size]
    print(batch)  # Affiche les lignes extraites pour vérification

    # Calculer le nouvel offset
    new_offset = offset + batch_size

    # Pousser le nouvel offset dans XComs
    context["task_instance"].xcom_push(key="offset", value=new_offset)

    # Pousser le DataFrame dans XComs
    context["task_instance"].xcom_push(key="dataframe", value=batch.to_json())

    return "Extraction terminée"


def transform_to_dict(**context):
    # Récupérer le DataFrame depuis les XComs
    df_json = context["task_instance"].xcom_pull(
        task_ids="extract_to_df", key="dataframe"
    )
    if not df_json:
        print("Aucune donnée à transformer.")
        return None

    # Convertir le JSON en DataFrame
    df = pd.read_json(df_json)
    data_dict = df.to_dict()
    print("Données transformées en dictionnaire :", data_dict)

    # Pousser le dictionnaire dans XComs
    context["task_instance"].xcom_push(key="dictionary", value=data_dict)

    return "Transformation terminée"


def log_dict(**context):
    # Récupérer le dictionnaire depuis les XComs
    data_dict = context["task_instance"].xcom_pull(
        task_ids="transform_to_dict", key="dictionary"
    )
    if not data_dict:
        print("Aucune donnée à afficher.")
        return None

    print("Données extraites et transformées :", data_dict)
    return "Affichage terminé"


default_args = {
    "owner": "airflow_user",
    "depends_on_past": False,
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
        task_id="extract_to_df",
        python_callable=extract_to_df,
        provide_context=True,
    )

    transform_task = PythonOperator(
        task_id="transform_to_dict",
        python_callable=transform_to_dict,
        provide_context=True,
    )

    log_task = PythonOperator(
        task_id="log_dict",
        python_callable=log_dict,
        provide_context=True,
    )

    extract_task >> transform_task >> log_task  # Définir l'ordre des tâches

# Le coeur de Airflow est de gérer les dépendances entre les tâches.
# Pour définir une tâche, il faut:
# - Spécifier le type de tâche (PythonOperator, BashOperator, MySQLOperator, etc.)
# - Lui donner un identifiant unique (task_id: str)
# - Spécifier la fonction à exécuter (python_callable: nom de la fonction)
# - Indiquer si le contexte doit être fourni (provide_context: bool, par défaut False)

#PRECISIONS:
# * * * * * # - Chaque astérisque représente une unité de temps (minute, heure, jour, mois, jour de la semaine).
# */: répétition d'une tâche à un intervalle régulier. (ex: "*/1" pour chaque minute)
# ,: séparation de plusieurs valeurs pour un champ (ex: "10,20,30" pour les minutes 10, 20 et 30).
# -: séparation de plusieurs valeurs pour un champ (ex: "1-5" pour les jours de la semaine du lundi au vendredi).
# *: valeur par défaut pour chaque unité de temps, signifiant "toutes les valeurs possibles" (ex: "*" pour chaque minute, heure, jour, etc.).
#  ex: "0,15,30,45 */2 1-5 * *" signifie : toutes les 15 min, toutes les 2 heures, les 5 premiers jours du mois, tous les mois
