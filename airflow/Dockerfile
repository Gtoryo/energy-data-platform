FROM apache/airflow:3.4.0-python3.11

# Un environnement virtuel par outil, séparé de celui d'Airflow,
# pour éviter les conflits de versions entre bibliothèques.
USER root
RUN mkdir /opt/venvs && chown airflow /opt/venvs
USER airflow

COPY requirements.txt /tmp/requirements-ingestion.txt
COPY dbt/requirements.txt /tmp/requirements-dbt.txt

RUN python -m venv /opt/venvs/ingestion \
    && /opt/venvs/ingestion/bin/pip install --no-cache-dir \
        -r /tmp/requirements-ingestion.txt \
    && python -m venv /opt/venvs/dbt \
    && /opt/venvs/dbt/bin/pip install --no-cache-dir \
        -r /tmp/requirements-dbt.txt
