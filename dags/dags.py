# dags/tmdb_dag.py
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import sys
import os
import logging

root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if root_path not in sys.path:
    sys.path.insert(0, root_path)

from setup.init_db import init_db
from pipeline.extract import extract
from pipeline.transform import transform
from pipeline.load import load

log = logging.getLogger(__name__)

default_args = {
    "owner": "kob",
    "retries": 1,
    "retry_delay": timedelta(minutes=1),
}


def run_extract(**context):
    log.info("Starting extraction from TMDB API")
    raw_df, genre_map = extract()
    context["ti"].xcom_push(key="raw_df", value=raw_df.to_json())
    context["ti"].xcom_push(key="genre_map", value=genre_map)
    log.info(f"Extracted {len(raw_df)} rows ✅")


def run_transform(**context):
    import pandas as pd
    from io import StringIO
    log.info("Starting transformation")

    raw_df = pd.read_json(StringIO(context["ti"].xcom_pull(key="raw_df")))
    genre_map = context["ti"].xcom_pull(key="genre_map")

    movies_df, movie_genres_df = transform(raw_df, genre_map)

    context["ti"].xcom_push(key="movies_df", value=movies_df.to_json())
    context["ti"].xcom_push(key="movie_genres_df", value=movie_genres_df.to_json())
    log.info(f"Transformed {len(movies_df)} movies, {len(movie_genres_df)} genre rows ✅")


def run_load(**context):
    import pandas as pd
    from io import StringIO
    log.info("Starting load to Neon PostgreSQL")

    movies_df = pd.read_json(StringIO(context["ti"].xcom_pull(key="movies_df")))
    movie_genres_df = pd.read_json(StringIO(context["ti"].xcom_pull(key="movie_genres_df")))

    movies_df["release_date"] = pd.to_datetime(movies_df["release_date"], unit="ms", errors="coerce").dt.date
    movies_df["scraped_at"] = pd.to_datetime(movies_df["scraped_at"], unit="ms", errors="coerce", utc=True)
    
    movies_df = movies_df.where(pd.notnull(movies_df), None)

    load(movies_df, movie_genres_df)
    log.info(f"Loaded {len(movies_df)} movies ✅")


with DAG(
    dag_id="tmdb_pipeline",
    default_args=default_args,
    description="Daily ETL pipeline for TMDB movie data",
    schedule_interval="@daily",
    start_date=datetime(2026, 4, 8),
    catchup=False,
    tags=["tmdb", "movies", "etl"],
) as dag:

    init_task = PythonOperator(
        task_id="init_db",
        python_callable=init_db,
    )

    extract_task = PythonOperator(
        task_id="extract",
        python_callable=run_extract,
    )

    transform_task = PythonOperator(
        task_id="transform",
        python_callable=run_transform,
    )

    load_task = PythonOperator(
        task_id="load",
        python_callable=run_load,
    )

    init_task >> extract_task >> transform_task >> load_task