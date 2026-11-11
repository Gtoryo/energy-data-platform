# Energy Data Platform -- Cahier des charges

**Version :** 1.1\
**Date de mise à jour :** 11 novembre 2026 (version 1.0 validée le 7 novembre 2026)\
**Statut :** Cahier des charges validé, mis à jour après l'étude technique de l'API\
**Périmètre :** Consommation et production d'électricité en France

### Historique des versions

  -----------------------------------------------------------------------
  Version     Date            Modifications
  ----------- --------------- -------------------------------------------
  1.0         7 nov. 2026     Version initiale validée.

  1.1         11 nov. 2026    Intégration des résultats de l'étude
                              technique de l'API (`docs/api_study.md`) :
                              sources, granularité, calcul de l'énergie,
                              unité carbone, changements d'heure, clé
                              métier, stratégie d'extraction, règles
                              RG13 à RG15, risques.
  -----------------------------------------------------------------------

------------------------------------------------------------------------

## 1. Présentation du projet

### 1.1 Contexte

La consommation électrique française évolue selon plusieurs facteurs :
saisons, conditions météorologiques, jours ouvrés, jours fériés,
activité économique, habitudes de consommation et disponibilité des
moyens de production.

Les données énergétiques publiques sont accessibles auprès de différents
organismes. Leur exploitation nécessite toutefois plusieurs opérations :
collecte, stockage, contrôle de qualité, transformation, historisation
et analyse.

### 1.2 Problématique

Comment concevoir une plateforme de données automatisée capable de
collecter, historiser, fiabiliser et exploiter les données de
consommation et de production électrique françaises afin de faciliter le
suivi des tendances énergétiques et leur analyse ?

### 1.3 Objectif général

Construire une plateforme de Data Engineering de bout en bout qui
récupère des données énergétiques françaises depuis une API publique,
les stocke dans PostgreSQL, les transforme avec dbt, orchestre les
traitements avec Apache Airflow et les expose dans Power BI.

Le projet servira également de support d'apprentissage pratique pour
Git, GitHub, Python, Requests, PostgreSQL, dbt, Docker, Airflow, pytest
et Power BI.

------------------------------------------------------------------------

## 2. Décisions de cadrage validées

  -----------------------------------------------------------------------
  Paramètre                           Décision
  ----------------------------------- -----------------------------------
  Nom du projet                       Energy Data Platform

  Domaine                             Électricité en France

  Historique cible                    Cinq ans glissants

  Fenêtre de référence initiale       Du 7 novembre 2021 au 7 novembre
                                      2026, sous réserve de disponibilité

  Granularité des observations        Grille source de 15 minutes ;
                                      mesures à 30 minutes (données
                                      définitives et consolidées) ou à
                                      15 minutes (temps réel) ;
                                      prévisions à 15 minutes

  Source principale                   RTE -- éCO₂mix national, via l'API
                                      ODRÉ : jeux
                                      `eco2mix-national-cons-def` et
                                      `eco2mix-national-tr`

  Stratégie d'extraction              Fenêtres mensuelles via l'endpoint
                                      d'export (`/exports/json`)

  Fréquence d'ingestion récurrente    Quotidienne

  Unités                              MW pour la puissance ; MWh pour
                                      l'énergie calculée ; g/kWh pour le
                                      taux de CO₂

  Stockage                            PostgreSQL

  Transformation                      dbt

  Orchestration                       Apache Airflow

  Conteneurisation                    Docker et Docker Compose

  Tests Python                        pytest

  Tests de données                    Tests dbt

  Visualisation                       Power BI

  Versioning                          Git et GitHub
  -----------------------------------------------------------------------

**Précision sur la période :** la fenêtre glissante de cinq ans est la
cible fonctionnelle. Les données réellement disponibles, leur statut
(provisoire, consolidé ou définitif) et leur granularité devront être
vérifiés dans la source avant l'extraction. Les années civiles complètes
pourront être utilisées pour certaines comparaisons, en signalant que
2026 est une année incomplète à la date de rédaction.

**Vérification (v1.1) :** la disponibilité a été confirmée par l'étude
technique. Les données sont définitives jusqu'au 31 décembre 2025,
consolidées du 1er janvier au 31 août 2026, et publiées en temps réel
au-delà (situation au 11 novembre 2026). Le détail figure dans
`docs/api_study.md`.

------------------------------------------------------------------------

## 3. Objectifs métier

  -----------------------------------------------------------------------
  Référence                           Objectif
  ----------------------------------- -----------------------------------
  OM01                                Suivre l'évolution de la
                                      consommation électrique française.

  OM02                                Identifier les périodes de forte et
                                      de faible consommation.

  OM03                                Analyser la contribution des
                                      différentes filières de production
                                      électrique.

  OM04                                Suivre l'évolution de l'intensité
                                      carbone associée à la production
                                      électrique.

  OM05                                Étudier les variations
                                      saisonnières, hebdomadaires et
                                      journalières.

  OM06                                Comparer la consommation réelle aux
                                      prévisions lorsqu'elles sont
                                      disponibles et comparables.

  OM07                                Identifier les périodes de forte
                                      contribution des énergies
                                      renouvelables.
  -----------------------------------------------------------------------

## 4. Objectifs techniques

  -----------------------------------------------------------------------
  Référence                           Objectif
  ----------------------------------- -----------------------------------
  OT01                                Développer un extracteur Python
                                      réutilisable avec Requests.

  OT02                                Mettre en place une ingestion
                                      fiable, traçable et idempotente.

  OT03                                Concevoir une architecture de
                                      stockage PostgreSQL en plusieurs
                                      couches.

  OT04                                Développer les transformations et
                                      modèles analytiques avec dbt.

  OT05                                Automatiser les traitements avec
                                      Apache Airflow.

  OT06                                Conteneuriser les composants avec
                                      Docker.

  OT07                                Tester le code Python avec pytest
                                      et les données avec dbt.

  OT08                                Mettre les données analytiques à
                                      disposition de Power BI.

  OT09                                Versionner le code et documenter
                                      les décisions avec Git et GitHub.
  -----------------------------------------------------------------------

------------------------------------------------------------------------

## 5. Périmètre fonctionnel et données

### 5.1 Source principale

La source principale envisagée est le jeu de données éCO₂mix national de
RTE, accessible par les ressources ouvertes de RTE et la plateforme
ODRÉ.

**Décision (v1.1), issue de l'étude technique (`docs/api_study.md`) :**
deux jeux de données ODRÉ sont nécessaires pour couvrir la fenêtre de
cinq ans :

-   `eco2mix-national-cons-def` : données définitives et consolidées
    (historique) ;
-   `eco2mix-national-tr` : données temps réel, du 1er septembre 2026
    jusqu'aux prévisions du lendemain.

Les deux jeux sont contigus. Une même période passe successivement du
statut temps réel au statut consolidé, puis définitif, et change alors
de jeu de données. L'accès se fait sans authentification. Les schémas
des deux jeux ne sont pas identiques : types déclarés différents pour
trois champs, et quatre champs présents uniquement en temps réel.

### 5.2 Familles de données visées

  -----------------------------------------------------------------------
  Famille                 Informations            Priorité
                          recherchées             
  ----------------------- ----------------------- -----------------------
  Consommation            Consommation électrique Haute
                          réalisée                

  Production nucléaire    Production nucléaire    Haute

  Production renouvelable Éolien, solaire et      Haute
                          hydraulique             

  Production thermique    Gaz, charbon, fioul et  Haute
                          bioénergies, selon      
                          disponibilité           

  Carbone                 Intensité ou émissions  Haute
                          de CO₂, selon les       
                          champs publiés          

  Échanges physiques      Importations et         Moyenne
                          exportations            

  Prévisions              Prévisions de           Moyenne
                          consommation            
                          disponibles             

  Stockage                Pompage (STEP) ;        Basse
                          batteries (temps réel   
                          uniquement)             
  -----------------------------------------------------------------------

La disponibilité de chaque champ, sa fréquence et son unité devront être
confirmées dans le contrat de données réel. Les observations réalisées à
30 minutes et les prévisions publiées à une autre fréquence ne devront
pas être mélangées sans traitement explicite.

### 5.3 Exemple pédagogique d'un enregistrement

L'exemple ci-dessous est fictif et sert uniquement à illustrer le type
d'information attendu. Il ne constitue pas le schéma officiel de l'API.
Le schéma réel est décrit au § 3 de `docs/api_study.md`.

``` json
{
  "date_heure": "2025-01-15T12:00:00+01:00",
  "nature": "Données consolidées",
  "consommation_mw": 72350,
  "nucleaire_mw": 45200,
  "eolien_mw": 8300,
  "solaire_mw": 2500,
  "hydraulique_mw": 9200,
  "gaz_mw": 3100,
  "charbon_mw": 0,
  "fioul_mw": 0,
  "bioenergies_mw": 950,
  "intensite_carbone": 35
}
```

### 5.4 Unités et granularité

-   Le MW mesure une puissance.
-   Le MWh mesure une quantité d'énergie.
-   Pour une puissance moyenne représentative d'un intervalle, l'énergie
    correspondante est estimée par :
    `énergie_MWh = puissance_MW × durée_intervalle_h`, soit 0,5 h pour
    une mesure à 30 minutes (données définitives et consolidées) et
    0,25 h pour une mesure à 15 minutes (temps réel). Un facteur fixe
    de 0,5 doublerait l'énergie calculée sur les données temps réel.
    Le caractère moyen (et non instantané) des mesures reste à
    confirmer dans la documentation RTE.
-   L'indicateur carbone publié est `taux_co2`, en g/kWh : estimation
    des émissions de carbone générées par la production d'électricité
    en France.
-   La grille source est de 15 minutes. Les mesures n'y sont remplies
    qu'une ligne sur deux pour les données définitives et consolidées,
    alors que les prévisions sont remplies à chaque ligne.
-   Les échanges commerciaux (`ech_comm_*`) sont des valeurs horaires
    recopiées sur plusieurs lignes : ils ne doivent pas être sommés
    sur des lignes infra-horaires.
-   Les données doivent conserver leur granularité d'origine et leur
    statut.

------------------------------------------------------------------------

## 6. Besoins fonctionnels

  -----------------------------------------------------------------------
  ID                      Fonctionnalité          Description
  ----------------------- ----------------------- -----------------------
  F01                     Extraction              Récupérer les données
                                                  depuis la source RTE
                                                  retenue.

  F02                     Pagination              Parcourir l'ensemble
                                                  des pages ou périodes
                                                  de résultats.

  F03                     Validation              Vérifier le format et
                                                  les champs attendus
                                                  avant chargement.

  F04                     Chargement              Enregistrer les données
                                                  reçues dans PostgreSQL.

  F05                     Transformation          Nettoyer, normaliser et
                                                  structurer les données
                                                  avec dbt.

  F06                     Qualité                 Contrôler les doublons,
                                                  valeurs manquantes et
                                                  incohérences.

  F07                     Orchestration           Planifier et exécuter
                                                  les traitements avec
                                                  Airflow.

  F08                     Tests                   Automatiser les tests
                                                  Python avec pytest et
                                                  les tests de données
                                                  avec dbt.

  F09                     Visualisation           Construire des
                                                  indicateurs et tableaux
                                                  de bord dans Power BI.

  F10                     Versioning              Gérer le code, les
                                                  branches et les
                                                  versions avec
                                                  Git/GitHub.
  -----------------------------------------------------------------------

## 7. Besoins non fonctionnels

-   **Fiabilité :** une erreur d'extraction ne doit pas entraîner la
    corruption des données déjà chargées.
-   **Traçabilité :** chaque lot doit permettre d'identifier la source
    et la date d'ingestion.
-   **Idempotence :** relancer un traitement ne doit pas créer de
    doublons ni dégrader les données.
-   **Maintenabilité :** chaque composant doit avoir une responsabilité
    clairement définie.
-   **Évolutivité :** l'architecture doit permettre d'ajouter d'autres
    sources ultérieurement.
-   **Sécurité :** les identifiants et secrets ne doivent jamais être
    versionnés dans Git.
-   **Testabilité :** les composants doivent pouvoir être testés
    indépendamment.
-   **Observabilité :** les erreurs, durées et volumes traités doivent
    être journalisés.

------------------------------------------------------------------------

## 8. Règles de gestion métier

  -----------------------------------------------------------------------
  ID                                  Règle
  ----------------------------------- -----------------------------------
  RG01                                Chaque observation doit posséder un
                                      horodatage exploitable.

  RG02                                Le périmètre géographique doit
                                      correspondre au périmètre national
                                      retenu.

  RG03                                La granularité et la nature des
                                      données sources doivent être
                                      conservées.

  RG04                                Les doublons selon la clé métier
                                      définie ne doivent pas subsister
                                      dans les tables analytiques.

  RG05                                Une valeur manquante ne doit pas
                                      être remplacée arbitrairement par
                                      zéro.

  RG06                                Les valeurs négatives doivent être
                                      interprétées selon leur
                                      signification métier avant d'être
                                      rejetées.

  RG07                                Le statut des données (par exemple
                                      provisoire, consolidé ou définitif)
                                      doit être conservé lorsqu'il est
                                      fourni.

  RG08                                Les corrections publiées par la
                                      source doivent pouvoir être
                                      réingérées sans créer de doublons.

  RG09                                Les horodatages doivent être gérés
                                      en tenant compte du fuseau
                                      Europe/Paris et des changements
                                      d'heure.

  RG10                                Les observations et les prévisions
                                      doivent être identifiables et
                                      séparées dans les analyses.

  RG11                                Les unités doivent être explicites
                                      et cohérentes dans les tables
                                      analytiques.

  RG12                                Les données sources brutes doivent
                                      rester traçables afin de pouvoir
                                      expliquer les transformations.

  RG13                                Les mesures sont converties
                                      explicitement en numérique,
                                      quel que soit le type déclaré par
                                      la source. Une valeur non
                                      convertible (par exemple `"ND"`)
                                      devient NULL et est tracée.

  RG14                                Une valeur horaire recopiée sur
                                      plusieurs lignes (échanges
                                      commerciaux) est ramenée à une
                                      valeur par heure avant toute
                                      agrégation.

  RG15                                Une ligne future du jeu temps réel
                                      ne contient que des prévisions :
                                      l'absence de mesure n'y constitue
                                      pas une anomalie de qualité.
  -----------------------------------------------------------------------

### 8.1 Idempotence et corrections

Une donnée publiée initialement peut être corrigée lors d'une
consolidation ultérieure. Le pipeline devra donc identifier une
observation à l'aide d'une clé métier adaptée au schéma réel (par
exemple horodatage, périmètre, type de donnée et nature de publication).

Le chargement devra permettre d'insérer les nouvelles observations et de
mettre à jour les observations corrigées, sans dupliquer les
enregistrements.

**Précision (v1.1) :** la nature de publication évolue dans le temps
pour un même instant (temps réel, puis consolidé, puis définitif). La
clé métier proposée est donc `date_heure` (UTC) + périmètre. La nature
devient un attribut de l'observation et non un élément de la clé. Quand
plusieurs versions existent, la priorité va à la donnée définitive, puis
consolidée, puis temps réel. Dans la couche RAW, l'unicité est assurée
par le couple
(jeu source, date locale, heure locale), car `date_heure` n'est pas
unique dans la source (voir § 8.2). Ces propositions seront validées
lors de la conception de la couche RAW.

### 8.2 Gestion des changements d'heure

Le fuseau Europe/Paris comporte des journées de 46 ou 50 intervalles de
30 minutes lors des changements d'heure, au lieu de 48 en journée
habituelle.

**Constat (v1.1) :** la source ne respecte pas ce principe. Elle publie
toujours 96 lignes de 15 minutes par jour local :

-   **en mars**, elle publie 4 lignes « fantômes » pour l'heure locale
    02:00--02:45, qui n'existe pas. Leur `date_heure` est identique à
    celle des lignes 03:00--03:45, ce qui crée 4 doublons d'horodatage
    UTC par an ;
-   **en octobre**, la première occurrence de l'heure locale répétée
    (00:00--00:45 UTC) est absente, soit 4 quarts d'heure manquants par
    an.

Le système devra :

-   utiliser `date_heure` (instant UTC) comme référence temporelle ;
-   préserver l'information permettant de restituer l'heure locale ;
-   supprimer les lignes fantômes, c'est-à-dire celles dont la date et
    l'heure locales ne correspondent pas à `date_heure` convertie dans
    le fuseau Europe/Paris ;
-   documenter l'heure manquante d'octobre comme un trou de la source,
    sans l'inventer ni l'interpoler ;
-   ne pas considérer automatiquement une journée de 92 ou 100 quarts
    d'heure réels comme incomplète.

------------------------------------------------------------------------

## 9. Indicateurs analytiques

Les indicateurs envisagés pour Power BI sont les suivants :

  -----------------------------------------------------------------------
  Indicateur                          Définition / utilisation
  ----------------------------------- -----------------------------------
  Puissance moyenne consommée         Moyenne de la puissance observée
                                      sur la période.

  Puissance maximale                  Valeur maximale observée sur la
                                      période.

  Puissance minimale                  Valeur minimale observée sur la
                                      période.

  Énergie estimée                     Somme des énergies calculées à
                                      partir des puissances et durées
                                      d'intervalle.

  Production par filière              Puissance ou énergie associée à
                                      chaque filière.

  Part du nucléaire                   Contribution du nucléaire à la
                                      production, selon une définition
                                      documentée.

  Part des renouvelables              Contribution des filières
                                      renouvelables retenues, selon une
                                      définition documentée.

  Intensité carbone moyenne           Moyenne de `taux_co2` (g/kWh) sur
                                      la période.

  Écart prévision/réel                Différence entre prévision et
                                      observation comparable sur le même
                                      intervalle.
  -----------------------------------------------------------------------

Les règles de calcul seront documentées dans dbt. Les indicateurs ne
seront pas calculés à partir de données de fréquences différentes sans
alignement temporel explicite.

### 9.1 Analyses attendues

1.  Évolution de la consommation par intervalle, jour, mois, trimestre
    et année.
2.  Comparaison des profils de consommation selon les jours de semaine
    et les saisons.
3.  Répartition de la production par filière.
4.  Évolution de l'intensité carbone.
5.  Comparaison entre consommation prévue et réalisée lorsque les
    données le permettent.
6.  Analyse de la contribution des énergies renouvelables.

------------------------------------------------------------------------

## 10. Architecture de données

L'entrepôt sera organisé en trois couches logiques dans PostgreSQL.

### 10.1 Couche RAW

**Schéma cible :** `raw`

Responsabilités : - conserver les données reçues de la source ; - tracer
la date et le lot d'ingestion ; - conserver les informations de
provenance ; - préserver le statut de publication lorsqu'il existe ; -
permettre la réconciliation de données corrigées.

La stratégie de conservation (colonnes structurées, réponse JSON brute
ou combinaison des deux) sera décidée lors de la conception de la couche
RAW. **Recommandation de l'étude technique (v1.1) :** conserver chaque
ligne telle que reçue (JSON brut), avec des colonnes techniques (jeu
source, fenêtre extraite, identifiant de lot, date d'ingestion). Les
types déclarés par l'API n'étant pas fiables, la conversion est reportée
en staging (RG13).

### 10.2 Couche STAGING

**Schéma cible :** `staging`

Responsabilités : - convertir les types ; - normaliser les horodatages
; - harmoniser les unités ; - standardiser les noms de champs ; -
traiter les valeurs manquantes selon les règles métier ; - identifier et
gérer les doublons.

### 10.3 Couche MART

**Schéma cible :** `analytics`

Responsabilités : - fournir des tables adaptées aux analyses ; -
construire les indicateurs ; - organiser les dimensions temporelles ; -
faciliter les connexions Power BI.

### 10.4 Modèle dimensionnel envisagé

  -----------------------------------------------------------------------
  Table                   Type                    Rôle
  ----------------------- ----------------------- -----------------------
  `fact_electricity`      Fait                    Mesures électriques par
                                                  intervalle et
                                                  périmètre.

  `dim_date`              Dimension               Date, année, mois,
                                                  trimestre, jour et
                                                  saison.

  `dim_time`              Dimension               Heure, minute et
                                                  tranche horaire.

  `dim_energy_source`     Dimension               Filière de production
                                                  et catégorie
                                                  énergétique.
  -----------------------------------------------------------------------

Le grain exact de chaque table sera défini après l'étude du contrat de
données. La production par filière pourra être représentée sous forme de
lignes associées à une dimension énergie, plutôt que par une colonne
fixe pour chaque filière.

------------------------------------------------------------------------

## 11. Orchestration avec Apache Airflow

Le DAG principal envisagé sera nommé `energy_data_pipeline`.

Ordre logique des tâches :

1.  `extract_energy_data` : appel de l'API et récupération des données.
2.  `validate_extracted_data` : validation du format et des champs.
3.  `load_raw_data` : chargement ou actualisation de la couche RAW.
4.  `run_dbt_staging` : exécution des transformations de staging.
5.  `run_dbt_marts` : construction des modèles analytiques.
6.  `run_quality_tests` : exécution des tests de données et contrôles
    finaux.

Airflow sera responsable de l'ordonnancement, des dépendances, des
reprises et du suivi des exécutions. Il ne remplacera ni le code
d'extraction Python, ni PostgreSQL, ni dbt.

### 11.1 Deux modes d'exécution

**Chargement initial historique (backfill)**

-   récupérer la fenêtre historique cible ;
-   découper l'extraction en fenêtres mensuelles semi-ouvertes
    `[début, fin[` via l'endpoint d'export, qui n'est pas soumis à la
    limite de 10 000 résultats de la pagination par offset ;
-   charger les données par lots (un lot par fenêtre) ;
-   contrôler les volumes et la couverture temporelle. Ordre de
    grandeur : environ 61 exports et 175 000 lignes pour cinq ans.

**Ingestion récurrente**

-   fréquence : quotidienne ;
-   récupérer les nouvelles données disponibles ;
-   réexaminer une fenêtre récente afin de prendre en compte les
    consolidations et corrections ;
-   exécuter les transformations et contrôles après le chargement.

**Taille des lots (v1.1) :** un mois. **Fenêtre de réconciliation
proposée :** relecture quotidienne de l'intégralité du jeu temps réel et
des douze derniers mois du jeu consolidé/définitif. Cette proposition
sera confirmée après observation de la fréquence de consolidation de la
source.

------------------------------------------------------------------------

## 12. Tests et qualité

### 12.1 Tests Python avec pytest

Les tests Python couvriront notamment : - la construction des requêtes
HTTP ; - la gestion des réponses et erreurs API ; - la pagination ; - la
validation du schéma reçu ; - la conversion et normalisation des données
; - la logique de chargement et d'upsert ; - les cas limites (réponse
vide, timeout, champ manquant, données invalides) ; - les journées de
changement d'heure (lignes fantômes de mars, heure manquante
d'octobre) ; - la conversion des valeurs non numériques (par exemple
`"ND"`).

Les appels externes seront simulés lorsque nécessaire afin de tester le
code sans dépendre de la disponibilité de l'API.

### 12.2 Tests dbt

Les tests dbt couvriront notamment : - `not_null` sur les champs
obligatoires ; - `unique` sur les clés adaptées ; - `relationships` sur
les clés étrangères ; - `accepted_values` sur les catégories contrôlées
; - des tests singuliers pour les règles métier spécifiques.

### 12.3 Contrôles opérationnels

Le pipeline devra journaliser : - le nombre de lignes reçues ; - le
nombre de lignes insérées ou mises à jour ; - la période couverte ; - la
date d'exécution ; - la durée des tâches ; - les erreurs et tentatives
de reprise.

------------------------------------------------------------------------

## 13. Infrastructure et conteneurisation

Docker et Docker Compose permettront de démarrer les services
nécessaires dans un environnement reproductible.

Les services envisagés sont : - PostgreSQL ; - Airflow (avec les
composants nécessaires à son exécution) ; - l'environnement Python
d'ingestion ; - l'environnement dbt.

Les versions des images et dépendances seront fixées. Les données
PostgreSQL et les journaux nécessaires seront persistés dans des volumes
adaptés.

Les secrets seront fournis via des variables d'environnement ou un
mécanisme de gestion adapté, sans être enregistrés dans le dépôt Git.

------------------------------------------------------------------------

## 14. Power BI

Power BI se connectera aux tables analytiques PostgreSQL.

Le tableau de bord initial devra présenter : - les principaux
indicateurs de consommation ; - l'évolution temporelle de la
consommation ; - les profils par jour et tranche horaire ; - le mix de
production électrique ; - l'évolution de l'intensité carbone ; - la
comparaison prévision/réel lorsque les données sont disponibles.

Les définitions des indicateurs devront être cohérentes avec celles
documentées dans dbt.

------------------------------------------------------------------------

## 15. Critères d'acceptation

  -----------------------------------------------------------------------
  ID                      Critère                 Résultat attendu
  ----------------------- ----------------------- -----------------------
  CA01                    Extraction API          Les données de la
                                                  période demandée sont
                                                  récupérées dans la
                                                  limite de leur
                                                  disponibilité.

  CA02                    Pagination              Toutes les pages ou
                                                  périodes attendues sont
                                                  parcourues.

  CA03                    Stockage                Les données sont
                                                  enregistrées dans
                                                  PostgreSQL avec leur
                                                  provenance.

  CA04                    Unicité                 Aucun doublon métier
                                                  non justifié ne
                                                  subsiste dans les
                                                  modèles analytiques.

  CA05                    Transformation          Les modèles dbt
                                                  s'exécutent
                                                  correctement.

  CA06                    Qualité                 Les tests dbt sont
                                                  satisfaits ou les
                                                  anomalies sont
                                                  documentées.

  CA07                    Orchestration           Le DAG Airflow
                                                  s'exécute selon le
                                                  calendrier défini.

  CA08                    Reprise                 Une tâche en échec peut
                                                  être relancée sans
                                                  corrompre les données.

  CA09                    Tests Python            Les tests pytest
                                                  passent.

  CA10                    Conteneurisation        L'environnement peut
                                                  être démarré avec
                                                  Docker Compose.

  CA11                    Power BI                Les indicateurs sont
                                                  accessibles et
                                                  cohérents avec
                                                  PostgreSQL.

  CA12                    Documentation           L'installation,
                                                  l'architecture et
                                                  l'exploitation sont
                                                  documentées.
  -----------------------------------------------------------------------

------------------------------------------------------------------------

## 16. Risques et mesures préventives

  -----------------------------------------------------------------------
  Risque                              Mesure préventive
  ----------------------------------- -----------------------------------
  API indisponible                    Timeouts, retries, gestion des
                                      erreurs et logs.

  Limitation des appels               Pagination, extraction par périodes
                                      et fréquence raisonnable.

  Données corrigées                   Réingestion et upsert idempotent.

  Valeurs manquantes                  Contrôles et documentation, sans
                                      remplacement arbitraire.

  Évolution du schéma API             Validation du contrat de données et
                                      tests de schéma.

  Volume historique important         Extraction par lots et suivi des
                                      volumes.

  Changements d'heure                 Gestion explicite des fuseaux et
                                      tests temporels ; suppression des
                                      lignes fantômes de mars et
                                      documentation de l'heure manquante
                                      d'octobre (§ 8.2).

  Types déclarés non fiables ou       Conversion explicite en staging et
  divergents entre les deux jeux      tests de valeurs non convertibles
                                      (RG13).

  Double comptage des valeurs         Ramener les échanges commerciaux à
  horaires recopiées                  une valeur par heure (RG14).

  Échec d'un DAG                      Reprise contrôlée et idempotence.

  Secrets exposés                     Variables d'environnement et
                                      `.gitignore`.
  -----------------------------------------------------------------------

Les conditions de réutilisation et d'attribution de la source officielle
devront être respectées et documentées. Les deux jeux sont publiés sous
Licence Ouverte v2.0 (Etalab), qui impose de mentionner la source et la
date de dernière mise à jour (voir § 11 de `docs/api_study.md`).

------------------------------------------------------------------------

## 17. Organisation du dépôt GitHub

Structure cible proposée :

``` text
energy-data-platform/
│
├── airflow/
│   ├── dags/
│   ├── plugins/
│   └── config/
│
├── ingestion/
│   ├── src/
│   │   ├── extract.py
│   │   ├── transform.py
│   │   ├── load.py
│   │   └── api_client.py
│   └── tests/
│
├── dbt/
│   └── energy_warehouse/
│       ├── models/
│       │   ├── staging/
│       │   └── marts/
│       ├── tests/
│       └── dbt_project.yml
│
├── database/
│   └── init/
│
├── powerbi/
│   └── dashboards/
│
├── docs/
│   ├── api_study.md
│   ├── architecture.md
│   ├── specifications.md
│   └── data_dictionary.md
│
├── exploration/          (scripts d'étude, hors production)
│
├── docker/
│
├── tests/
│
├── .env.example
├── .gitignore
├── docker-compose.yml
├── requirements.txt
└── README.md
```

### Stratégie de branches

-   `main` : version stable.
-   `develop` : branche d'intégration.
-   `feature/<nom>` : développement d'une fonctionnalité.

Les commits devront être explicites et les décisions techniques
importantes documentées.

------------------------------------------------------------------------

## 18. Étapes de réalisation

  -----------------------------------------------------------------------
  Étape                   Travail                 Livrable
  ----------------------- ----------------------- -----------------------
  1                       Étude technique de      Contrat de données et
                          l'API RTE               endpoints validés

  2                       Initialisation          Dépôt structuré
                          Git/GitHub              

  3                       Développement Python    Extracteur fonctionnel

  4                       Conception PostgreSQL   Base et schémas
                                                  initialisés

  5                       Chargement historique   Couche RAW alimentée

  6                       Développement dbt       Modèles et tests

  7                       Conteneurisation Docker Infrastructure
                                                  reproductible

  8                       Développement Airflow   DAG opérationnel

  9                       Tests pytest            Tests automatisés

  10                      Power BI                Tableau de bord

  11                      Documentation et        Projet finalisé
                          validation              
  -----------------------------------------------------------------------

L'ordre pourra être ajusté selon les dépendances techniques découvertes
pendant la réalisation.

------------------------------------------------------------------------

## 19. Livrables finaux

À la fin du projet, les livrables attendus seront :

-   Un dépôt GitHub documenté.
-   Un extracteur Python réutilisable.
-   Une base PostgreSQL organisée en couches.
-   Un projet dbt avec modèles et tests.
-   Un ou plusieurs DAG Airflow opérationnels.
-   Une infrastructure Docker Compose.
-   Une suite de tests pytest.
-   Un tableau de bord Power BI.
-   Une documentation d'architecture, d'installation et d'exploitation.
-   Un dictionnaire de données et les définitions des indicateurs.

------------------------------------------------------------------------

## 20. Prochaine étape

L'étude technique de la source (étape 1) est réalisée. Ses résultats,
ses décisions et ses questions ouvertes sont consignés dans
`docs/api_study.md`. Elle a couvert les sept points prévus : jeux de
données, endpoints et authentification, paramètres et filtres
temporels, pagination, schéma réel, unités, statuts et fuseaux
horaires, limites d'utilisation et licence.

La prochaine étape est la conception de la couche RAW (grain, clé
d'unicité, colonnes techniques), qui permettra de valider les
propositions P1 à P3 de l'étude, puis le développement de l'extracteur
définitif.

**Principe de travail :** chaque étape sera expliquée avant son
implémentation. Le code ne sera pas simplement fourni ; les choix
techniques, les responsabilités des composants et les interactions entre
technologies seront explicités.
