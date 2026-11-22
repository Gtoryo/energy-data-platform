"""Client HTTP de l'API Opendatasoft (ODRÉ) pour les jeux éCO2mix."""

import time

import requests

BASE_URL = "https://odre.opendatasoft.com/api/explore/v2.1/catalog/datasets"
RETRY_STATUSES = (429, 500, 502, 503, 504)
NETWORK_ERRORS = (
    requests.exceptions.Timeout,
    requests.exceptions.ConnectionError,
)


def build_export_params(start, end):
    """Construit les paramètres d'export de la fenêtre [start, end[."""
    return {
        "where": (
            f'date_heure >= "{start.isoformat()}" '
            f'and date_heure < "{end.isoformat()}"'
        ),
        "order_by": "date_heure",
    }


def fetch_window(dataset, start, end, max_retries=3):
    """Télécharge toutes les lignes d'un jeu dans la fenêtre [start, end[."""
    url = f"{BASE_URL}/{dataset}/exports/json"
    return get_json(url, build_export_params(start, end), max_retries)


def get_json(url, params, max_retries=3):
    """Envoie une requête GET et renvoie le JSON reçu.

    Les erreurs temporaires donnent lieu à de nouvelles tentatives.
    """
    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(url, params=params, timeout=60)
        except NETWORK_ERRORS:
            if wait_before_retry(attempt, max_retries):
                continue
            raise

        if response.status_code == 200:
            return response.json()

        if response.status_code in RETRY_STATUSES:
            retry_after = response.headers.get("Retry-After")
            if wait_before_retry(attempt, max_retries, retry_after):
                continue

        response.raise_for_status()
        raise RuntimeError(f"Statut HTTP inattendu : {response.status_code}")


def wait_before_retry(attempt, max_retries, retry_after=None):
    """Attend avant une nouvelle tentative.

    Renvoie True si une nouvelle tentative est autorisée, False sinon.
    """
    if attempt >= max_retries:
        return False
    delay = 2 * 2 ** (attempt - 1)
    if retry_after is not None:
        try:
            delay = float(retry_after)
        except ValueError:
            pass

    time.sleep(delay)
    return True
