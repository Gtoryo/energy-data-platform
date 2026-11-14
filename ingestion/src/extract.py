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
