"""Écriture des données extraites dans la couche RAW."""

import os
from datetime import date, time

import psycopg
from psycopg.types.json import Jsonb

UPSERT_SQL = """
    INSERT INTO raw.eco2mix_national AS r
        (jeu, date_locale, heure_locale, payload, lot_id)
    VALUES (%s, %s, %s, %s, %s)
    ON CONFLICT (jeu, date_locale, heure_locale) DO UPDATE
    SET payload = EXCLUDED.payload,
        lot_id = EXCLUDED.lot_id,
        modifie_le = now()
    WHERE r.payload IS DISTINCT FROM EXCLUDED.payload
    RETURNING old.lot_id IS NULL AS inserted
"""


def connect():
    """Ouvre une connexion à PostgreSQL en mode autocommit.

    Les paramètres viennent des variables d'environnement POSTGRES_*.
    """
    return psycopg.connect(
        host=os.environ["POSTGRES_HOST"],
        port=os.environ["POSTGRES_PORT"],
        dbname=os.environ["POSTGRES_DB"],
        user=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
        connect_timeout=10,
        autocommit=True,
    )


def open_lot(conn, dataset, start, end):
    """Enregistre un lot au statut en_cours et renvoie son numéro."""
    row = conn.execute(
        "INSERT INTO raw.lots_ingestion (jeu, fenetre_debut, fenetre_fin) "
        "VALUES (%s, %s, %s) RETURNING lot_id",
        (dataset, start, end),
    ).fetchone()
    return row[0]


def upsert_records(conn, dataset, records, lot_id):
    """Écrit les enregistrements dans RAW, en une seule transaction.

    Renvoie le nombre de lignes insérées et le nombre de lignes modifiées.
    """
    inserted = updated = 0
    with conn.transaction():
        for record in records:
            row = conn.execute(
                UPSERT_SQL,
                (
                    dataset,
                    date.fromisoformat(record["date"]),
                    time.fromisoformat(record["heure"]),
                    Jsonb(record),
                    lot_id,
                ),
            ).fetchone()
            if row is None:
                continue
            if row[0]:
                inserted += 1
            else:
                updated += 1
    return inserted, updated


def close_lot(
    conn,
    lot_id,
    status,
    received=None,
    inserted=None,
    updated=None,
    error=None,
):
    """Termine un lot avec son statut, ses compteurs et l'erreur éventuelle."""
    conn.execute(
        "UPDATE raw.lots_ingestion "
        "SET statut = %s, termine_le = now(), nb_lignes_recues = %s, "
        "nb_lignes_inserees = %s, nb_lignes_modifiees = %s, "
        "message_erreur = %s "
        "WHERE lot_id = %s",
        (status, received, inserted, updated, error, lot_id),
    )
