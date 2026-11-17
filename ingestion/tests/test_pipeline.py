from datetime import datetime

import pytest
import requests

import api_client
import pipeline
from extract import PARIS

DATASET = "test-dataset"
START = datetime(2025, 1, 1, tzinfo=PARIS)
END = datetime(2025, 2, 1, tzinfo=PARIS)
RECORDS = [
    {"date": "2025-01-15", "heure": "12:00", "consommation": 70000},
    {"date": "2025-01-15", "heure": "12:15", "consommation": 70500},
]


def fetch_lots(conn):
    """Renvoie tous les lots du jeu de test, du plus ancien au plus récent."""
    return conn.execute(
        "SELECT statut, nb_lignes_recues, nb_lignes_inserees, "
        "nb_lignes_modifiees, message_erreur "
        "FROM raw.lots_ingestion WHERE jeu = %s ORDER BY lot_id",
        (DATASET,),
    ).fetchall()


def count_rows(conn):
    return conn.execute(
        "SELECT count(*) FROM raw.eco2mix_national WHERE jeu = %s",
        (DATASET,),
    ).fetchone()[0]


def test_successful_run_closes_lot_with_counters(conn, monkeypatch):
    def fake_fetch(dataset, start, end):
        return RECORDS

    monkeypatch.setattr(api_client, "fetch_window", fake_fetch)

    pipeline.run_window(conn, DATASET, START, END)

    assert fetch_lots(conn) == [("succes", 2, 2, 0, None)]
    assert count_rows(conn) == 2


def test_api_failure_is_recorded_and_raised(conn, monkeypatch):
    def failing_fetch(dataset, start, end):
        raise requests.HTTPError("503 Server Error")

    monkeypatch.setattr(api_client, "fetch_window", failing_fetch)

    with pytest.raises(requests.HTTPError):
        pipeline.run_window(conn, DATASET, START, END)

    assert fetch_lots(conn) == [
        ("echec", None, None, None, "HTTPError: 503 Server Error")
    ]


def test_empty_window_is_a_failure(conn, monkeypatch):
    def empty_fetch(dataset, start, end):
        return []

    monkeypatch.setattr(api_client, "fetch_window", empty_fetch)

    with pytest.raises(RuntimeError):
        pipeline.run_window(conn, DATASET, START, END)

    error = "RuntimeError: Aucune ligne reçue pour cette fenêtre"
    assert fetch_lots(conn) == [("echec", None, None, None, error)]



def test_load_failure_keeps_lot_but_no_rows(conn, monkeypatch):
    broken = RECORDS + [{"date": "2025-01-15", "heure": "pas une heure"}]

    def fake_fetch(dataset, start, end):
        return broken

    monkeypatch.setattr(api_client, "fetch_window", fake_fetch)

    with pytest.raises(ValueError):
        pipeline.run_window(conn, DATASET, START, END)

    error = "ValueError: Invalid isoformat string: 'pas une heure'"
    assert fetch_lots(conn) == [("echec", None, None, None, error)]
    assert count_rows(conn) == 0
