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
    Une fenêtre vide est un échec : la source doit renvoyer des lignes.
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


def recent_months(dataset, count):
    """Renvoie le premier et le dernier des `count` derniers mois publiés.

    Le dernier mois est celui de la dernière date publiée, en heure de Paris.
    """
    last_date = api_client.fetch_last_date(dataset).astimezone(extract.PARIS)
    last_month = datetime(last_date.year, last_date.month, 1)
    return extract.months_before(last_month, count - 1), last_month


def main():
    """Charge dans RAW tous les mois d'une période, un lot par mois."""
    parser = argparse.ArgumentParser(
        description="Charge des mois éCO2mix dans la couche RAW."
    )
    parser.add_argument(
    "first_month", type=parse_month, nargs="?", help="AAAA-MM"
    )
    parser.add_argument(
        "last_month", type=parse_month, nargs="?", help="AAAA-MM"
    )
    parser.add_argument(
        "--recent",
        type=int,
        metavar="N",
        help="relit les N derniers mois publiés, au lieu d'une période",
    )
    args = parser.parse_args()

    if args.recent and not args.first_month:
        first_month, last_month = recent_months(args.dataset, args.recent)
    elif args.first_month and args.last_month and not args.recent:
        first_month, last_month = args.first_month, args.last_month
    else:
        parser.error("donner une période AAAA-MM AAAA-MM ou --recent N")

    load_dotenv()
    windows = extract.monthly_windows(first_month, last_month)

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
