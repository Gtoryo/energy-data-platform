"""Profilage des jeux de données éCO2mix national (étude de l'API ODORÉ)."""

import json
import time

import requests

BASE_URL = "https://odre.opendatasoft.com/api/explore/v2.1/catalog/datasets"
DATASETS = ["eco2mix-national-cons-def", "eco2mix-national-tr"]
DEBUT_FENETRE = "2021-11-07T00:00:00+01:00"


def get(url, params=None):
    response = requests.get(url, params=params, timeout=60)
    response.raise_for_status()
    return response.json()


def afficher(titre, donnees):
    print(f"\n=== {titre} ===")
    print(json.dumps(donnees, indent=2, ensure_ascii=False))


def schema(dataset):
    meta = get(f"{BASE_URL}/{dataset}")
    return {champ["name"]: champ["type"] for champ in meta["fields"]}


def couverture(dataset):
    params = {
        "select": (
            "nature, min(date_heure) as debut, max(date_heure) as fin, "
            "count(*) as nb_lignes"
        ),
        "group_by": "nature",
    }
    return get(f"{BASE_URL}/{dataset}/records", params)["results"]


def remplissage_par_minute(dataset):
    params = {
        "select": (
            "count(*) as nb_lignes, count(consommation) as nb_conso, "
            "count(prevision_j1) as nb_prev_j1"
        ),
        "where": f'date_heure >= "{DEBUT_FENETRE}"',
        "group_by": "minute(date_heure) as minute",
    }
    return get(f"{BASE_URL}/{dataset}/records", params)["results"]


def echantillon(dataset, n=4):
    params = {
        "limit": n,
        "order_by": "date_heure",
        "where": f'date_heure >= "{DEBUT_FENETRE}"',
    }
    return get(f"{BASE_URL}/{dataset}/records", params)["results"]


def mesurer_export(dataset, debut, fin):
    params = {"where": f'date_heure >= "{debut}" and date_heure < "{fin}"'}
    t0 = time.perf_counter()
    lignes = get(f"{BASE_URL}/{dataset}/exports/json", params)
    duree = time.perf_counter() - t0
    return {"nb_lignes": len(lignes), "duree_s": round(duree, 2)}


def journee(dataset, jour):
    params = {
        "select": "heure, date_heure, consommation",
        "where": f'date = "{jour}"',
        "order_by": "date_heure",
        "limit": 100,
    }
    return get(f"{BASE_URL}/{dataset}/records", params)["results"]


if __name__ == "__main__":
    for dataset in DATASETS:
        afficher(f"{dataset} : schéma", schema(dataset))
        afficher(f"{dataset} : couverture", couverture(dataset))
        afficher(f"{dataset} : remplissage", remplissage_par_minute(dataset))
        afficher(f"{dataset} : échantillon", echantillon(dataset))


    afficher(
        "Export d'un mois (janvier 2025)",
        mesurer_export(
            "eco2mix-national-cons-def",
            "2025-01-01T00:00:00+01:00",
            "2025-02-01T00:00:00+01:00",
        ),
    )


    jours_changement_heure = [
            ("eco2mix-national-cons-def", "2025-03-30"),
            ("eco2mix-national-cons-def", "2025-10-26"),
            ("eco2mix-national-tr", "2026-10-25"),
        ]
    for dataset, jour in jours_changement_heure:
        afficher(f"{dataset} : changement d'heure du {jour}", journee(dataset, jour))

