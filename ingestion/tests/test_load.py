from datetime import datetime

import pytest

import load
from extract import PARIS

DATASET = "test-dataset"
START = datetime(2025, 1, 1, tzinfo=PARIS)
END = datetime(2025, 2, 1, tzinfo=PARIS)
RECORDS = [
    {"date": "2025-01-15", "heure": "12:00", "consommation": 70000},
    {"date": "2025-01-15", "heure": "12:15", "consommation": None},
    {"date": "2025-01-15", "heure": "12:30", "consommation": 71000},
]


def fetch_lot(conn, lot_id):
    return conn.execute(
        "SELECT statut, nb_lignes_recues, nb_lignes_inserees, "
        "nb_lignes_modifiees, message_erreur "
        "FROM raw.lots_ingestion WHERE lot_id = %s",
        (lot_id,),
    ).fetchone()


def test_open_lot_starts_in_progress(conn):
    lot_id = load.open_lot(conn, DATASET, START, END)
    assert fetch_lot(conn, lot_id) == ("en_cours", None, None, None, None)


def test_first_load_inserts_all_records(conn):
    lot_id = load.open_lot(conn, DATASET, START, END)
    assert load.upsert_records(conn, DATASET, RECORDS, lot_id) == (3, 0)


def test_reload_of_identical_records_changes_nothing(conn):
    lot_id = load.open_lot(conn, DATASET, START, END)
    load.upsert_records(conn, DATASET, RECORDS, lot_id)
    assert load.upsert_records(conn, DATASET, RECORDS, lot_id) == (0, 0)


def test_reload_updates_only_corrected_record(conn):
    lot_id = load.open_lot(conn, DATASET, START, END)
    load.upsert_records(conn, DATASET, RECORDS, lot_id)

    corrected = [dict(record) for record in RECORDS]
    corrected[2]["consommation"] = 71200
    assert load.upsert_records(conn, DATASET, corrected, lot_id) == (0, 1)

    value = conn.execute(
        "SELECT payload->>'consommation' FROM raw.eco2mix_national "
        "WHERE jeu = %s AND heure_locale = '12:30'",
        (DATASET,),
    ).fetchone()[0]
    assert value == "71200"


def test_failed_load_writes_nothing(conn):
    lot_id = load.open_lot(conn, DATASET, START, END)
    broken = RECORDS + [{"date": "2025-01-15", "heure": "pas une heure"}]

    with pytest.raises(ValueError):
        load.upsert_records(conn, DATASET, broken, lot_id)

    count = conn.execute(
        "SELECT count(*) FROM raw.eco2mix_national WHERE jeu = %s",
        (DATASET,),
    ).fetchone()[0]
    assert count == 0


def test_close_lot_records_status_and_counters(conn):
    lot_id = load.open_lot(conn, DATASET, START, END)
    load.close_lot(conn, lot_id, "succes", received=3, inserted=3, updated=0)
    assert fetch_lot(conn, lot_id) == ("succes", 3, 3, 0, None)
