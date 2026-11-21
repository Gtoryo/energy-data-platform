# Architecture de la plateforme

Version 1.2 du 21/11/2026. Ce document décrit l'architecture technique de la plateforme et justifie les choix de conception. Il complète le cahier des charges (`docs/specifications.md`) et l'étude de l'API (`docs/api_study.md`).

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

À ce jour, la couche RAW, l'extraction et le chargement ainsi que les couches staging et analytics sont réalisés, et l'historique de cinq ans est chargé. L'orchestration et la restitution restent à construire.

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

## Transformation (dbt)

### Rôle

Le projet dbt du dossier `dbt/energy_warehouse` construit les couches staging et analytics à partir de RAW. Les transformations sont écrites en SQL et s'exécutent à l'intérieur de PostgreSQL. Une seule commande construit tous les modèles et exécute tous les tests, dans l'ordre de leurs dépendances :

```bash
cd dbt/energy_warehouse
dbt build
```

dbt utilise les mêmes variables `POSTGRES_*` que le code Python. En local, il lit lui-même le fichier `.env`. Le fichier `profiles.yml` est versionné, car il ne contient que des références à ces variables, jamais leurs valeurs. Les versions sont figées dans `dbt/requirements.txt` : dbt-core 1.12.7 et dbt-postgres 1.11.0. dbt 2 ne prend pas encore PostgreSQL en charge.

### Modèles

| Modèle | Schéma et forme | Une ligne représente |
|---|---|---|
| `stg_eco2mix` | `staging`, vue | une ligne de `raw.eco2mix_national`, avec ses mesures typées |
| `stg_eco2mix_instants` | `staging`, vue | un instant (`date_heure`) dans sa version la plus fiable, hors lignes fantômes |
| `fct_consommation` | `analytics`, table | un instant où la consommation est mesurée |
| `fct_production` | `analytics`, table | un instant mesuré et une filière de production |
| `dim_filiere` | `analytics`, table chargée depuis un fichier CSV (seed) | une filière de production |
| `dim_date` | `analytics`, table | un jour du calendrier |

Les tables de faits se relient aux dimensions par la colonne `date` (vers `dim_date`) et par la colonne `filiere` (vers `dim_filiere`). C'est un schéma en étoile, la forme attendue par Power BI.

### Décisions

- **Vues en staging, tables en analytics.** Une vue ne stocke rien et reflète toujours le contenu de RAW. Les tables analytics sont calculées à chaque `dbt build`, puis lues rapidement par Power BI. Par défaut, dbt aurait nommé le schéma analytics `staging_analytics`, en ajoutant au schéma du profil celui demandé par le modèle. La macro `macros/generate_schema_name.sql` utilise le nom demandé tel quel, pour retrouver les trois schémas de l'entrepôt.
- **Conversion tolérante des mesures, stricte des horodatages.** Une mesure n'est convertie en `numeric` que si sa valeur est un nombre valide (`pg_input_is_valid`). Sinon, elle devient NULL (RG13). Sur cinq ans, une seule valeur est concernée (`"ND"`), mais une conversion directe faisait échouer tout le modèle. À l'inverse, `date_heure` est convertie sans tolérance : un horodatage invalide doit arrêter la construction (RG01). La liste des 36 mesures est écrite une seule fois, et une boucle Jinja génère leurs conversions.
- **Une ligne par instant.** Une ligne est « fantôme » quand sa date et son heure locales ne correspondent pas à sa `date_heure` convertie en heure de Paris (RG09). Les 20 lignes concernées sont marquées dans `stg_eco2mix` (`est_fantome`), qui reste fidèle à RAW, puis exclues de `stg_eco2mix_instants`. Quand un instant existe en plusieurs versions, ce modèle garde la plus fiable : définitive, puis consolidée, puis temps réel. Aujourd'hui, les deux jeux ne se chevauchent pas. Cette règle servira quand `cons-def` couvrira des mois déjà chargés depuis `tr`. La nature retenue reste visible dans les tables de faits (RG07), et `date_heure` y est unique (RG04).
- **Énergie = puissance × durée.** La source publie des puissances moyennes, en MW. Les données consolidées et définitives sont mesurées toutes les demi-heures, et les données temps réel tous les quarts d'heure. La durée d'un intervalle (`duree_h`) vaut donc 0,5 h ou 0,25 h. Cette règle est définie à un seul endroit, `stg_eco2mix_instants`, et les deux tables de faits la réutilisent. Les instants sans mesure ne sont pas comptés comme des zéros : ils sont écartés des tables de faits (RG05). Ce sont les quarts d'heure intermédiaires de `cons-def` et les instants futurs de `tr`, qui ne portent que des prévisions (RG15). Les unités figurent dans le nom des colonnes : `consommation_mw`, `consommation_mwh`, `taux_co2_g_par_kwh` (RG11).
- **Deux tables de faits, dont la production au format long.** Le cahier des charges envisageait une table de faits unique (§10.4). Or la consommation (une ligne par instant) et la production (une ligne par instant et par filière) n'ont pas le même grain. Dans une table commune, la consommation serait répétée sur chaque ligne de filière, et une somme la compterait huit fois. `fct_production` contient une ligne par filière plutôt qu'une colonne par filière, comme le recommandait le cahier des charges. Power BI peut ainsi ventiler la production par filière ou par catégorie avec une seule mesure. Les 8 filières principales sont retenues. Leur détail (éolien terrestre et en mer, types de centrales à gaz, etc.) reste disponible en staging.
- **Filières décrites dans un seed.** `dim_filiere` est appelée `dim_energy_source` dans le cahier des charges. C'est un fichier CSV versionné, car le classement des filières est une convention qui doit être écrite et relue. Il suit celui de RTE, qui compte comme renouvelables l'hydraulique, y compris le turbinage des STEP, et les bioénergies, y compris l'incinération des déchets. Le nucléaire est classé bas carbone, mais non renouvelable.
- **Calendrier en années complètes.** `dim_date` va du 1er janvier de la première année de données au 31 décembre de la dernière. Ses bornes sont lues dans les données, et elle s'étend d'elle-même quand une nouvelle année est chargée. Elle respecte les quatre règles d'une table de dates Power BI : dates uniques, non vides, sans trou et en années complètes. Les noms des mois et des jours viennent de listes écrites dans le modèle, et non de `to_char`, qui écrit dans la langue du serveur (ici l'anglais). Les saisons sont météorologiques : décembre à février pour l'hiver, et ainsi de suite. La dimension `dim_time` envisagée par le cahier des charges n'a pas été créée : l'heure locale est une colonne des tables de faits.

### Validation

**Tests automatisés : 17 tests dbt**, exécutés par `dbt build` après chaque modèle.

| Test | Modèles | Ce qui est garanti |
|---|---|---|
| `unique`, `not_null` sur `date_heure` | `stg_eco2mix_instants`, `fct_consommation` | Un seul enregistrement par instant (RG04). |
| `not_null` sur `rang_nature` | `stg_eco2mix` | Toutes les natures reçues sont connues. Une nature nouvelle ou mal orthographiée est signalée. |
| `not_null` sur `consommation_mwh` et `production_mwh` | tables de faits | Chaque ligne de fait porte son énergie. |
| `unique`, `not_null` sur les clés | `dim_date`, `dim_filiere` | Une jointure vers une dimension ne duplique aucun fait. |
| `relationships` sur `date` et `filiere`, `not_null` sur `filiere` | tables de faits | Chaque fait trouve sa date et sa filière : aucune ligne orpheline dans Power BI. `relationships` ignore les valeurs vides, d'où le `not_null`. |
| `assert_jours_de_24_heures_au_plus` | `fct_consommation` | Aucun jour ne cumule plus de 24 h de mesures : la durée des intervalles est juste. |
| `assert_dim_date_continue` | `dim_date` | Le calendrier est sans trou et couvre des années complètes. |

Chaque test a été volontairement saboté pour vérifier qu'il échoue. Cette pratique a révélé un test de `dim_filiere` qui visait une colonne inexistante portant le nom de la table. PostgreSQL lisait ce nom comme la ligne entière, et le test réussissait sans rien vérifier. Il a été corrigé.

**Volumes au 20/11/2026.**

| Modèle | Lignes |
|---|---|
| `stg_eco2mix` | 177 024, autant que RAW |
| `stg_eco2mix_instants` | 177 004, après exclusion des 20 lignes fantômes |
| `fct_consommation` | 92 195 |
| `fct_production` | 737 560, soit 92 195 instants × 8 filières |
| `dim_filiere` | 8 |
| `dim_date` | 2 191, de 2021 à 2026 |

Contrôles de vraisemblance :

- **Consommation annuelle.** 450,1 TWh en 2022, 435,5 en 2023, 440,0 en 2024 et 443,8 en 2025.
- **Production 2024 par catégorie.** Nucléaire 361,7 TWh, renouvelable 156,8 TWh et fossile 19,2 TWh, des valeurs cohérentes avec le bilan électrique 2024 publié par RTE.
- **Solde.** En 2022, la production (443,3 TWh) est inférieure à la consommation : c'est l'année où une grande partie du parc nucléaire était à l'arrêt, et où la France a importé de l'électricité. Les années suivantes, la production dépasse nettement la consommation, et la France exporte.
- **Durée mesurée par jour.** 24 h, sauf au passage à l'heure d'été (23 h) et pour les jours incomplets à la source.
- **Saisonnalité.** En 2024, la puissance moyenne consommée atteint 61 610 MW en hiver, contre 42 647 MW en été : la consommation française dépend fortement de la température, à cause du chauffage électrique. Elle baisse aussi le week-end : 45 746 MW en moyenne le dimanche, contre 52 080 MW le mardi.

### Limites

- **Trace des valeurs non convertibles.** RG13 demande que les valeurs converties en NULL soient tracées. Elles ne sont pas encore comptées ni signalées.
- **Prévisions futures.** Les tables de faits ne contiennent que des instants mesurés. Les prévisions des instants à venir, publiées dans `tr`, ne sont pas encore exposées en analytics (RG10).
- **Mesures restées en staging.** Les échanges commerciaux (RG14), le stockage (pompage, batteries) et le détail des filières ne sont pas encore repris en analytics.
