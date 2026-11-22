"""Pipeline quotidien : chargement de RAW, puis construction de l'entrepôt."""

import logging
from datetime import timedelta
from zoneinfo import ZoneInfo

import pendulum
from airflow.providers.standard.operators.bash import BashOperator
from airflow.sdk import DAG

log = logging.getLogger(__name__)


def mois_a_relire(instant):
    """Renvoie le mois précédent et le mois courant, au format AAAA-MM.

    Le calcul se fait en heure de Paris. Reculer d'un jour depuis le 1er
    du mois donne toujours le mois précédent, même en janvier.
    """
    premier = instant.astimezone(ZoneInfo("Europe/Paris")).replace(day=1)
    veille = premier - timedelta(days=1)
    return f"{veille:%Y-%m} {premier:%Y-%m}"


def alerter(context):
    """Signale l'échec définitif d'une tâche, après toutes ses reprises."""
    ti = context["ti"]
    log.error(
        "ALERTE : la tâche %s du DAG %s a échoué définitivement (run %s).",
        ti.task_id,
        ti.dag_id,
        context["run_id"],
    )


with DAG(
    dag_id="energy_data_pipeline",
    schedule=None,
    start_date=pendulum.datetime(2026, 11, 1, tz="Europe/Paris"),
    default_args={
        "retries": 2,
        "retry_delay": timedelta(minutes=5),
        "on_failure_callback": alerter,
    },
    user_defined_macros={"mois_a_relire": mois_a_relire},
    tags=["production"],
):
    load_raw_tr = BashOperator(
        task_id="load_raw_tr",
        bash_command=(
            "/opt/venvs/ingestion/bin/python pipeline.py eco2mix-national-tr"
            " {{ mois_a_relire(dag_run.run_after) }}"
        ),
        cwd="/opt/project/ingestion/src",
    )
    dbt_build = BashOperator(
        task_id="dbt_build",
        bash_command="/opt/venvs/dbt/bin/dbt build",
        cwd="/opt/project/dbt/energy_warehouse",
    )

    load_raw_tr >> dbt_build
