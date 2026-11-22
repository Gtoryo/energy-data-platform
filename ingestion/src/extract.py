"""Découpage de la période à extraire en fenêtres mensuelles"""

from datetime import datetime
from zoneinfo import ZoneInfo

PARIS = ZoneInfo("Europe/Paris")


def monthly_windows(first_month, last_month):
    """Renvoie les fenêtres mensuelles [début, fin[ entre deux mois inclus.

    Seuls l'année et le mois des deux dates comptent.
    Chaque borne est un datetime à minuit, heure de Paris.
    """
    first = (first_month.year, first_month.month)
    last = (last_month.year, last_month.month)
    if first > last:
        raise ValueError("first_month doit précéder last_month")

    windows = []
    year, month = first
    while (year, month) <= last:
        start = datetime(year, month, 1, tzinfo=PARIS)
        if month == 12:
            year, month = year + 1, 1
        else:
            month += 1
        end = datetime(year, month, 1, tzinfo=PARIS)
        windows.append((start, end))
    return windows


def months_before(month, count):
    """Renvoie le 1er du mois situé `count` mois avant `month`.

    Seuls l'année et le mois de `month` comptent. Les mois sont numérotés
    à la suite (année × 12 + mois), ce qui gère le passage d'année.
    """
    index = month.year * 12 + month.month - 1 - count
    return datetime(index // 12, index % 12 + 1, 1)
