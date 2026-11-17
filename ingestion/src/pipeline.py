"""Extraction puis chargement d'une fenêtre, avec tenue du carnet."""

import api_client
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
