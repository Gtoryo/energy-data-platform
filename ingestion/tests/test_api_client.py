from datetime import datetime, timezone

import pytest
import requests

import api_client
from extract import PARIS

DATASET = "eco2mix-national-cons-def"
START = datetime(2025, 3, 1, tzinfo=PARIS)
END = datetime(2025, 4, 1, tzinfo=PARIS)


class FakeResponse:
    """Fausse réponse HTTP : seulement ce qu'utilise fetch_window."""

    def __init__(self, status_code, data=None, headers=None):
        self.status_code = status_code
        self.data = data
        self.headers = headers or {}

    def json(self):
        return self.data

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.exceptions.HTTPError(f"HTTP {self.status_code}")


def install_fake_api(monkeypatch, responses):
    """Remplace requests.get et time.sleep le temps d'un test.

    Renvoie la liste des URL appelées et celle des attentes demandées.
    """
    urls = []
    sleeps = []

    def fake_get(url, params=None, timeout=None):
        urls.append(url)
        response = responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response

    monkeypatch.setattr(api_client.requests, "get", fake_get)
    monkeypatch.setattr(api_client.time, "sleep", sleeps.append)
    return urls, sleeps


def test_export_params_use_half_open_window():
    params = api_client.build_export_params(START, END)
    assert params["where"] == (
        'date_heure >= "2025-03-01T00:00:00+01:00" '
        'and date_heure < "2025-04-01T00:00:00+02:00"'
    )


def test_returns_rows_on_success(monkeypatch):
    rows = [{"date": "2025-03-01", "heure": "00:00"}]
    urls, sleeps = install_fake_api(monkeypatch, [FakeResponse(200, rows)])

    assert api_client.fetch_window(DATASET, START, END) == rows
    assert urls[0].endswith(f"/{DATASET}/exports/json")
    assert sleeps == []


def test_retries_after_server_error(monkeypatch):
    responses = [FakeResponse(503), FakeResponse(200, [])]
    urls, sleeps = install_fake_api(monkeypatch, responses)

    assert api_client.fetch_window(DATASET, START, END) == []
    assert sleeps == [2]


def test_follows_retry_after_header(monkeypatch):
    responses = [
        FakeResponse(429, headers={"Retry-After": "5"}),
        FakeResponse(200, []),
    ]
    urls, sleeps = install_fake_api(monkeypatch, responses)

    api_client.fetch_window(DATASET, START, END)
    assert sleeps == [5.0]


def test_retries_after_network_error(monkeypatch):
    responses = [requests.exceptions.ConnectionError(), FakeResponse(200, [])]
    urls, sleeps = install_fake_api(monkeypatch, responses)

    assert api_client.fetch_window(DATASET, START, END) == []
    assert len(urls) == 2


def test_gives_up_after_max_retries(monkeypatch):
    responses = [FakeResponse(503), FakeResponse(503), FakeResponse(503)]
    urls, sleeps = install_fake_api(monkeypatch, responses)

    with pytest.raises(requests.exceptions.HTTPError):
        api_client.fetch_window(DATASET, START, END)
    assert sleeps == [2, 4]


def test_does_not_retry_client_error(monkeypatch):
    urls, sleeps = install_fake_api(monkeypatch, [FakeResponse(404)])

    with pytest.raises(requests.exceptions.HTTPError):
        api_client.fetch_window(DATASET, START, END)
    assert len(urls) == 1


def test_fetch_last_date_reads_the_maximum(monkeypatch):
    data = {"results": [{"fin": "2026-08-31T21:45:00+00:00"}]}
    urls, sleeps = install_fake_api(monkeypatch, [FakeResponse(200, data)])

    last = api_client.fetch_last_date(DATASET)
    assert last == datetime(2026, 8, 31, 21, 45, tzinfo=timezone.utc)
    assert urls[0].endswith(f"/{DATASET}/records")


def test_fetch_last_date_fails_without_data(monkeypatch):
    data = {"results": [{"fin": None}]}
    install_fake_api(monkeypatch, [FakeResponse(200, data)])

    with pytest.raises(RuntimeError):
        api_client.fetch_last_date(DATASET)
