# Energy Data Platform -- Cahier des charges

**Version :** 1.0\
**Date de validation :** 7 novembre 2026\
**Statut :** Cahier des charges validé\
**Périmètre :** Consommation et production d'électricité en France

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

  Granularité des observations        30 minutes lorsque disponible

  Source principale                   RTE -- éCO₂mix, via les ressources
                                      ouvertes et l'API documentée

  Fréquence d'ingestion récurrente    Quotidienne

  Unités                              MW pour la puissance ; MWh pour
                                      l'énergie calculée

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

La sélection exacte du jeu de données, de l'endpoint et du mode d'accès
sera confirmée pendant l'étude technique de l'API. Nous vérifierons
notamment la documentation, les paramètres, la pagination, les limites
d'appel, le schéma de réponse, les unités, les fuseaux horaires et les
conditions de réutilisation.

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
  -----------------------------------------------------------------------

La disponibilité de chaque champ, sa fréquence et son unité devront être
confirmées dans le contrat de données réel. Les observations réalisées à
30 minutes et les prévisions publiées à une autre fréquence ne devront
pas être mélangées sans traitement explicite.

### 5.3 Exemple pédagogique d'un enregistrement

L'exemple ci-dessous est fictif et sert uniquement à illustrer le type
d'information attendu. Il ne constitue pas le schéma officiel de l'API.

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
-   Pour une puissance moyenne représentative d'un intervalle de 30
    minutes, l'énergie correspondante peut être estimée par :
    `énergie_MWh = puissance_MW × 0,5`.
-   L'unité et la définition exactes de l'indicateur carbone devront
    être reprises de la documentation officielle.
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
  -----------------------------------------------------------------------

### 8.1 Idempotence et corrections

Une donnée publiée initialement peut être corrigée lors d'une
consolidation ultérieure. Le pipeline devra donc identifier une
observation à l'aide d'une clé métier adaptée au schéma réel (par
exemple horodatage, périmètre, type de donnée et nature de publication).

Le chargement devra permettre d'insérer les nouvelles observations et de
mettre à jour les observations corrigées, sans dupliquer les
enregistrements.

### 8.2 Gestion des changements d'heure

Le fuseau Europe/Paris comporte des journées de 46 ou 50 intervalles de
30 minutes lors des changements d'heure, au lieu de 48 en journée
habituelle.

Le système devra : - conserver un horodatage avec fuseau ou un instant
UTC non ambigu ; - préserver l'information permettant de restituer
l'heure locale ; - distinguer les deux occurrences d'une heure locale
répétée en automne ; - ne pas considérer automatiquement une journée de
46 ou 50 intervalles comme incomplète.

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

  Intensité carbone moyenne           Moyenne calculée selon la
                                      définition et l'unité de la source.

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
ou combinaison des deux) sera décidée après inspection du schéma API.

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
-   découper l'extraction en périodes adaptées aux limites de l'API ;
-   charger les données par lots ;
-   contrôler les volumes et la couverture temporelle.

**Ingestion récurrente**

-   fréquence : quotidienne ;
-   récupérer les nouvelles données disponibles ;
-   réexaminer une fenêtre récente afin de prendre en compte les
    consolidations et corrections ;
-   exécuter les transformations et contrôles après le chargement.

La taille exacte des lots et de la fenêtre de réconciliation sera
décidée après les tests de l'API et l'observation de ses délais de
publication.

------------------------------------------------------------------------

## 12. Tests et qualité

### 12.1 Tests Python avec pytest

Les tests Python couvriront notamment : - la construction des requêtes
HTTP ; - la gestion des réponses et erreurs API ; - la pagination ; - la
validation du schéma reçu ; - la conversion et normalisation des données
; - la logique de chargement et d'upsert ; - les cas limites (réponse
vide, timeout, champ manquant, données invalides).

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
                                      tests temporels.

  Échec d'un DAG                      Reprise contrôlée et idempotence.

  Secrets exposés                     Variables d'environnement et
                                      `.gitignore`.
  -----------------------------------------------------------------------

Les conditions de réutilisation et d'attribution de la source officielle
devront être respectées et documentées.

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
│   ├── architecture.md
│   ├── specifications.md
│   └── data_dictionary.md
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

## 20. Prochaine étape : étude technique de l'API RTE

Le cahier des charges étant validé, la prochaine étape est l'étude
technique de la source de données.

Nous allons examiner concrètement :

1.  Le jeu de données RTE exact à utiliser.
2.  Les endpoints et méthodes d'authentification éventuelles.
3.  Les paramètres de requête et filtres temporels.
4.  Le mécanisme de pagination.
5.  Le schéma réel des réponses.
6.  Les unités, statuts et fuseaux horaires.
7.  Les limites d'utilisation et conditions de réutilisation.

Après cette étude, nous écrirons un premier script Python avec Requests
pour interroger l'API, examiner la réponse et valider notre
compréhension des données avant de construire l'extracteur définitif.

**Principe de travail :** chaque étape sera expliquée avant son
implémentation. Le code ne sera pas simplement fourni ; les choix
techniques, les responsabilités des composants et les interactions entre
technologies seront explicités.
