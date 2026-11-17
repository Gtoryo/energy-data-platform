"""Fixtures partargées pas tous les fichiers de tests."""

import pytest
from dotenv import load_dotenv

import load


@pytest.fixture
def conn():
    """Connexion dont tout le travail est annulé à la fin du test."""
    load_dotenv()
    with load.connect() as connection:
        with connection.transaction(force_rollback=True):
            yield connection
