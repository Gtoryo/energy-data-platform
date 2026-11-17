"""Extraction puis chargement d'une fenêtre, avec tenue du carnet."""

import argparse
import time
from datetime import datetime

from dotenv import load_dotenv

import api_client
import extract
import load


def run_window(conn, dataset, start, end):
    """Extrait une fenêtre de l'API et la charge dans RAW.

    Le lot est fermé en succès ou en échec. En cas d'échec, l'erreur
    est enregistrée dans le carnet, puis relancée.
    Renvoie le numéro du lot.
    """
    lot_id = load.open_lot(conn, dataset, start, end)
    try:
        records = api_client.fetch_window(dataset, start, end)
        if not records:
            raise RuntimeError("Aucune ligne reçue pour cette fenêtre")
        inserted, updated = load.upsert_records(conn, dataset, records, lot_id)
    except Exception as error:
        message = f"{type(error).__name__}: {error}"
        load.close_lot(conn, lot_id, "echec", error=message)
        raise
    load.close_lot(
        conn,
        lot_id,
        "succes",
        received=len(records),
        inserted=inserted,
        updated=updated,
    )
    return lot_id


def parse_month(text):
    """Convertit un mois au format AAAA-MM en datetime."""
    return datetime.strptime(text, "%Y-%m")


def main():
    """Charge dans RAW tous les mois d'une période, un lot par mois."""
    parser = argparse.ArgumentParser(
        description="Charge des mois éCO2mix dans la couche RAW."
    )
    parser.add_argument("dataset", help="jeu de données de l'API")
    parser.add_argument("first_month", type=parse_month, help="AAAA-MM")
    parser.add_argument("last_month", type=parse_month, help="AAAA-MM")
    args = parser.parse_args()

    load_dotenv()
    windows = extract.monthly_windows(args.first_month, args.last_month)
    with load.connect() as conn:
        for number, (start, end) in enumerate(windows, start=1):
            began = time.perf_counter()
            lot_id = run_window(conn, args.dataset, start, end)
            elapsed = time.perf_counter() - began
            print(
                f"[{number}/{len(windows)}] {start:%Y-%m} : "
                f"lot {lot_id} en {elapsed:.1f} s",
                flush=True,
            )


if __name__ == "__main__":
    main()
