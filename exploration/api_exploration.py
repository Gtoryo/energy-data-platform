import requests
import time

API_URL = (
    "https://reseaux-energies-rte.opendatasoft.com/api/explore/v2.1/"
    "catalog/datasets/eco2mix-national-cons-def/records"
)


def fetch_page(offset, limit, max_retries=3):

    params = {

        "limit": limit,
        "offset": offset,
        "order_by": "date_heure DESC"
    }


    for tentative in range(1, max_retries + 1):

        try:
            response = requests.get(
                API_URL,
                params=params,
                timeout=30
            )
    
            if response.status_code == 200:
                return response.json()["results"]
    
            elif response.status_code in (429, 500, 502, 503, 504):

                retry_after = None

                if response.status_code == 429:
                    retry_after = response.headers.get("Retry-After")

                if wait_before_retry(tentative, max_retries, retry_after):
                    continue

                else:
                    response.raise_for_status()

            else:
                response.raise_for_status()

        except (
            requests.exceptions.Timeout,
            requests.exceptions.ConnectionError
        ):
           if wait_before_retry(tentative, max_retries):
               continue
           else:
               response.raise_for_status()
               raise RuntimeError(
                   f"Status HTTP inattendu : {response.status_code}"
               )



def extract_data():

    limit = 100
    offset = 0
    records = []
    max_records = 250

    while True:

        remaining = max_records - len(records)

        if remaining <= 0:
            break

        current_limit = min(limit, remaining)

        results = fetch_page(
            offset=offset,
            limit=current_limit
        )

        nombre_recupere = len(results)

        if nombre_recupere == 0:
            break

        records.extend(results)

        offset += nombre_recupere
        
    return records



def wait_before_retry(tentative, max_retries, retry_after=None):
    """Attend avant une nouvelle tentative.
    
    Renvoie True si une nouvelle tentative est autorisée, False sinon.
    """

    if tentative >= max_retries:
        return False

    delai_initial = 2
    delai = delai_initial * 2 ** (tentative - 1)

    if retry_after is not None:
        try:
            delai = float(retry_after)
        except ValueError:
            pass


    time.sleep(delai)
    return True