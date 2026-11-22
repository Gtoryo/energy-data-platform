"""Vérifie les outils installés et l'accès à l'entrepôt."""

import pendulum
from airflow.providers.standard.operators.bash import BashOperator
from airflow.sdk import DAG

with DAG(
    dag_id="check_environment",
    schedule=None,
    start_date=pendulum.datetime(2026, 11, 1, tz="Europe/Paris"),
    tags=["maintenance"],
):
    versions = BashOperator(
        task_id="versions",
        bash_command=(
            "/opt/venvs/ingestion/bin/python --version"
            " && /opt/venvs/dbt/bin/dbt --version"
        ),
    )
    connexion = BashOperator(
        task_id="connexion_entrepot",
        bash_command="/opt/venvs/dbt/bin/dbt debug",
        cwd="/opt/project/dbt/energy_warehouse",
    )

    versions >> connexion
