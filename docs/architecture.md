# Architecture de la plateforme

Version 1.0 du 14/11/2026. Ce document décrit l'architecture technique de la plateforme et justifie les choix de conception. Il complète le cahier des charges (`docs/specifications.md`) et l'étude de l'API (`docs/api_study.md`).

## Vue d'ensemble

La plateforme suit une approche **ELT** : les données sont extraites de la source, chargées telles quelles dans l'entrepôt, puis transformées à l'intérieur de celui-ci.

| Étape | Outil | Rôle |
|---|---|---|
| Extraction et chargement | Python | Récupère les données de consommation et de production d'électricité publiées par éCO2mix (API ODRÉ) et les charge dans la couche RAW. |
| Stockage | PostgreSQL | Entrepôt organisé en trois schémas (voir ci-dessous). |
| Transformation | dbt | Construit les couches staging et analytics à partir de RAW. |
| Orchestration | Airflow | Planifie et enchaîne les traitements. |
| Restitution | Power BI | Tableaux de bord. |

L'entrepôt PostgreSQL comporte un schéma par couche :

- `raw` : copie fidèle des données reçues de la source ;
- `staging` : données typées, nettoyées et dédoublonnées ;
- `analytics` : tables prêtes pour l'analyse et Power BI.

À ce jour, seule la couche RAW est réalisée.

## Couche RAW

### Rôle

RAW conserve une copie fidèle de ce que l'API a renvoyé. C'est le filet de sécurité de la plateforme : si une transformation est fausse, staging et analytics sont reconstruits à partir de RAW, sans rappeler l'API. RAW ne nettoie, ne corrige et ne supprime rien, y compris les lignes connues comme erronées (lignes fantômes de mars). En résumé : **RAW garde, staging décide.**

### Tables

| Table | Une ligne représente | Clé |
|---|---|---|
| `raw.lots_ingestion` | un chargement : un jeu de données et une fenêtre de temps | `lot_id`, attribué par PostgreSQL |
| `raw.eco2mix_national` | un enregistrement de la source, dans sa dernière version reçue | `(jeu, date_locale, heure_locale)` |

Chaque ligne de données porte le numéro du dernier lot qui l'a écrite (`lot_id`), sa date d'insertion (`insere_le`) et sa date de dernière modification (`modifie_le`, vide si la ligne n'a jamais changé). La fenêtre extraite est enregistrée une seule fois, dans le lot, au lieu d'être répétée sur chaque ligne. Le script de création est `database/init/01_raw.sql`.

### Décisions

- **Format JSONB.** Chaque enregistrement est stocké tel que reçu, dans une colonne `payload` de type JSONB, plutôt que dans des colonnes typées. Les types de la source ne sont pas fiables (valeur `"ND"`, champs `text` ou `int` selon le jeu), et les deux jeux n'ont pas les mêmes champs. Une colonne typée ferait échouer le chargement, alors qu'avec JSONB le chargement continue de fonctionner même si RTE ajoute un champ. Le typage est fait en staging (RG13). JSONB est préféré à JSON, car son stockage binaire permet de le comparer et de l'indexer.
- **Clé `(jeu, date_locale, heure_locale)` plutôt que `date_heure`.** Chaque année en mars, la source publie 4 lignes « fantômes » dont la `date_heure` est identique à celle de vraies lignes (20 doublons sur 5 ans) : `date_heure` n'est donc pas unique. Le jeu fait partie de la clé, car un même quart d'heure peut exister dans `tr` puis dans `cons-def`. Les colonnes de la clé sont typées (`date`, `time`) : une clé invalide fait échouer le chargement au lieu d'enregistrer une ligne inutilisable.
- **Idempotence par upsert avec détection de changement.** Le chargement utilise `INSERT … ON CONFLICT … DO UPDATE`. Les nouvelles lignes sont insérées, les lignes modifiées par la source sont mises à jour, et les lignes identiques ne sont pas touchées (`WHERE payload IS DISTINCT FROM …`). Relancer un chargement est donc sans danger et ne réécrit rien inutilement.
- **Un lot = une transaction.** Les données d'un lot sont écrites entièrement ou pas du tout : un chargement interrompu n'en laisse aucune partie. Le carnet `raw.lots_ingestion` est écrit hors de cette transaction, pour que la trace d'un échec survive à l'annulation.

### Validation

Tests manuels réalisés le 14/11/2026 sur PostgreSQL 18.7 :

| Test | Résultat |
|---|---|
| Statut invalide, fenêtre inversée, lot inexistant | Refusés par les contraintes (`CHECK`, clé étrangère). |
| Premier chargement de 3 lignes | `INSERT 0 3` |
| Rechargement des 3 lignes, dont une corrigée par la source | `INSERT 0 1` : les 2 lignes identiques sont ignorées, seule la ligne corrigée est modifiée. |
| Chargement annulé par `ROLLBACK` | Aucune donnée écrite ; le lot est enregistré avec le statut `echec`. |
