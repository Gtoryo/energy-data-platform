# Architecture de la plateforme

Version 1.1 du 18/11/2026. Ce document décrit l'architecture technique de la plateforme et justifie les choix de conception. Il complète le cahier des charges (`docs/specifications.md`) et l'étude de l'API (`docs/api_study.md`).

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

À ce jour, la couche RAW ainsi que l'extraction et le chargement sont réalisés, et l'historique de cinq ans est chargé. Les couches staging et analytics, l'orchestration et la restitution restent à construire.

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

## Extraction et chargement

### Rôle

Le code Python du dossier `ingestion/src` télécharge les données de l'API par fenêtres mensuelles et les écrit dans la couche RAW, à raison d'un lot par fenêtre. Il se lance avec une commande qui reçoit un jeu de données et une période :

```bash
python ingestion/src/pipeline.py eco2mix-national-cons-def 2021-11 2026-08
```

Les paramètres de connexion à PostgreSQL sont lus dans les variables d'environnement `POSTGRES_*`. En local, elles viennent du fichier `.env`, qui n'est pas versionné ; `.env.example` en donne le modèle.

### Modules

| Module | Responsabilité |
|---|---|
| `extract.py` | Découpe une période en fenêtres mensuelles `[début, fin[`. |
| `api_client.py` | Télécharge une fenêtre par l'endpoint d'export de l'API, avec nouvelles tentatives. |
| `load.py` | Écrit dans RAW : ouverture du lot, upsert des lignes, fermeture du lot. |
| `pipeline.py` | Enchaîne téléchargement et écriture pour chaque fenêtre, tient le carnet des lots et fournit la commande. |

Seul `pipeline.py` connaît les autres modules : `api_client.py` ignore tout de la base, et `load.py` ignore tout de l'API. Chaque module peut ainsi être testé seul.

### Décisions

- **Fenêtres mensuelles en heure de Paris.** Chaque fenêtre va de minuit le 1er du mois (inclus) à minuit le 1er du mois suivant (exclu), heure de Paris. Deux fenêtres voisines se touchent sans se chevaucher : aucune ligne n'est perdue ni lue deux fois. L'endpoint d'export n'est pas limité à 10 000 lignes, contrairement à la pagination de `/records`, et un mois (environ 3 000 lignes) donne un lot de taille raisonnable. Le premier mois est chargé en entier, ce qui couvre la fenêtre de référence, qui commence le 7 novembre 2021.
- **Nouvelles tentatives ciblées.** Une erreur temporaire (statut 429, 500, 502, 503 ou 504, délai dépassé, connexion impossible) donne lieu à de nouvelles tentatives, jusqu'à 3 essais au total, après 2 s puis 4 s d'attente. Si l'API envoie l'en-tête `Retry-After`, son délai est respecté. Les autres erreurs 4xx ne sont pas retentées : elles signalent une requête incorrecte, qu'un nouvel essai ne corrigerait pas. Chaque requête HTTP est limitée à 60 s, et la connexion à la base à 10 s : le pipeline n'attend jamais indéfiniment.
- **Une fenêtre vide est un échec.** Une réponse `200` ne garantit pas la présence des données. Le 17/11/2026, lors d'un essai de chargement complet, l'API a répondu `200` avec une liste vide pour 11 mois de `cons-def`, entre 16:06:19 et 16:06:55 UTC. La source retraitait alors le jeu : ses métadonnées indiquent une republication à 16:07:14 UTC. Quelques minutes plus tard, ces mois étaient complets. Sans contrôle, ces lots auraient été enregistrés en succès, et les mois auraient manqué sans alerte. Toute fenêtre demandée par le pipeline doit contenir des données : une réponse vide fait donc échouer le lot.
- **Un échec arrête la commande.** En cas d'erreur, le lot passe au statut `echec` avec le message de l'erreur, puis l'erreur est relancée. La commande s'arrête alors avec le code de sortie 1, qu'un orchestrateur peut détecter. Relancer la même commande est sans danger grâce à l'upsert : les mois déjà chargés ne sont pas modifiés. Un lot resté `en_cours` signale une exécution interrompue (Ctrl+C, arrêt de la machine).
- **Connexion à `127.0.0.1` plutôt qu'à `localhost`.** Sur le poste de développement, `localhost` tente d'abord l'adresse IPv6 `::1`, alors que le port de PostgreSQL n'est publié que sur `127.0.0.1`. Chaque connexion attendait environ 8 s, contre 0,03 s avec l'adresse explicite.

### Validation

**Tests automatisés : 22 tests pytest.**

| Type | Fichiers | Ce qui est vérifié |
|---|---|---|
| Unitaires (12) | `test_extract.py`, `test_api_client.py` | Découpage des fenêtres (changement d'année, changement d'heure), paramètres d'export, nouvelles tentatives et abandon. Une fausse API remplace le réseau. |
| Intégration (10) | `test_load.py`, `test_pipeline.py` | Insertion, rechargement sans changement, détection d'une correction, annulation d'un lot en erreur, tenue du carnet en succès et en échec, fenêtre vide. Ces tests utilisent la vraie base PostgreSQL : chacun s'exécute dans une transaction annulée à la fin, sans laisser de trace. |

Les tests d'intégration nécessitent que le conteneur PostgreSQL soit démarré. Chaque garde-fou important a été volontairement saboté pour vérifier que son test échoue.

**Chargement initial du 17/11/2026.**

| Jeu | Période | Lots | Lignes | Durée |
|---|---|---|---|---|
| `eco2mix-national-cons-def` | 2021-11 à 2026-08 | 58, tous en succès | 169 440 | 4 min 43 s |
| `eco2mix-national-tr` | 2026-09 à 2026-11 | 3, tous en succès | 7 584 | 12 s |

Contrôles réalisés après le chargement :

- **Volumes.** Un mois complet compte 96 quarts d'heure par jour, y compris lors des changements d'heure : en mars, les 4 lignes fantômes compensent l'heure qui n'existe pas ; en octobre, la source omet 4 quarts d'heure de l'heure qui se répète. Tous les mois respectent cette règle, sauf novembre 2026 pour `tr`, mois en cours (1 728 lignes sur 2 880).
- **Couverture.** `cons-def` couvre la période du 01/11/2021 au 31/08/2026, et `tr` celle du 01/09/2026 au lendemain du chargement (prévisions J+1). Les deux jeux se raccordent sans trou.
- **Idempotence.** Le rechargement de mars 2025 a reçu 2 976 lignes, sans en insérer ni en modifier aucune.
- **Détection des changements.** Lors d'un essai préalable, deux chargements de `tr` espacés d'environ dix minutes ont détecté 24 lignes corrigées par la source. Cela confirme l'intérêt de relire régulièrement les données récentes (proposition P3 de l'étude de l'API).
