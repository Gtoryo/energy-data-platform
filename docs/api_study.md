# Étude technique de l'API éCO2mix

**Version :** 1.0 — 11 novembre 2026\
**Statut :** étude réalisée. Décisions D1 et D2 validées ; propositions P1 à P3 à valider lors de la conception de la couche RAW.\
**Script de référence :** `exploration/profilage_api.py`

> Tous les chiffres de ce document ont été mesurés sur l'API les 10 et 11 novembre 2026,
> sur la fenêtre du 7 novembre 2021 au 12 novembre 2026. Les dates sont exprimées en
> **heure de Paris** sauf mention explicite « UTC ».

---

## 1. Sources retenues

| Identifiant ODRÉ | Titre | Natures publiées | Rôle dans le projet |
|---|---|---|---|
| `eco2mix-national-cons-def` | Données éCO2mix nationales consolidées et définitives | Données définitives, Données consolidées | Historique |
| `eco2mix-national-tr` | Données éCO2mix nationales temps réel | Données temps réel | Données récentes et prévisions du lendemain |

Producteur : **RTE**. Diffuseur : **ODRÉ** (Open Data Réseaux Énergies). Périmètre : `France` uniquement (100 % des lignes).

Aucun des deux jeux ne couvre seul la fenêtre cible de 5 ans : il faut **les deux** (voir § 4).

## 2. Accès et endpoints

**URL de base :** `https://odre.opendatasoft.com/api/explore/v2.1/catalog/datasets`

L'ancien domaine `reseaux-energies-rte.opendatasoft.com` répond encore, mais ce n'est pas l'adresse documentée : il ne doit pas être utilisé.

**Authentification :** aucune.

| Endpoint | Usage | Limites constatées |
|---|---|---|
| `GET /{dataset}` | Métadonnées : schéma, types, licence | — |
| `GET /{dataset}/records` | Requêtes ODSQL, agrégations, échantillons | `limit` ≤ 100 ; `offset + limit` ≤ 10 000 (erreur `InvalidRESTParameterError` au-delà) |
| `GET /{dataset}/exports/json` | Export complet du résultat filtré | Pas de pagination, pas de plafond de lignes constaté |

**Paramètres ODSQL utilisés :** `select`, `where`, `group_by`, `order_by`, `limit`, `offset`. Les dates d'un filtre `where` se placent entre guillemets doubles, avec leur décalage horaire explicite :

```text
where = date_heure >= "2025-01-01T00:00:00+01:00" and date_heure < "2025-02-01T00:00:00+01:00"
```

**Quota :** les en-têtes de réponse indiquent `X-RateLimit-Limit: 10000000`, remis à zéro à 00:00 UTC. Ce plafond n'est pas contraignant pour le projet, qui fait au plus quelques dizaines d'appels par jour.

## 3. Schéma des champs

Toutes les puissances sont en **MW**. Le type indiqué est celui que déclare l'API.

| Groupe | Champs | Type API | Remarques |
|---|---|---|---|
| Identification | `perimetre`, `nature` | text | `perimetre` = `France` |
| Temps (local) | `date` (`AAAA-MM-JJ`), `heure` (`HH:MM`) | text | Heure **de Paris** |
| Temps (UTC) | `date_heure` | datetime | ISO 8601 en **UTC** (`+00:00`) |
| Consommation | `consommation` | int | Consommation réalisée |
| Prévisions | `prevision_j1`, `prevision_j` | int | Prévision faite la veille (J-1) et le jour même (J) |
| Production par filière | `nucleaire`, `eolien`, `solaire`, `hydraulique`, `gaz`, `charbon`, `fioul`, `bioenergies` | int | Agrégats par filière |
| Détail par technologie | `fioul_tac`, `fioul_cogen`, `fioul_autres`, `gaz_tac`, `gaz_cogen`, `gaz_ccg`, `gaz_autres`, `hydraulique_fil_eau_eclusee`, `hydraulique_lacs`, `hydraulique_step_turbinage`, `bioenergies_dechets`, `bioenergies_biomasse`, `bioenergies_biogaz` | int (voir exceptions) | Sous-détail des filières |
| Stockage | `pompage` | int | Puissance consommée par les pompes des STEP : **toujours ≤ 0** |
| Échanges | `ech_physiques` | int | Solde physique aux frontières : **négatif = export**, positif = import |
| Échanges commerciaux | `ech_comm_angleterre`, `ech_comm_espagne`, `ech_comm_italie`, `ech_comm_suisse`, `ech_comm_allemagne_belgique` | int (voir exceptions) | Même convention de signe. **Valeurs horaires** (voir § 5) |
| Carbone | `taux_co2` | int | **g/kWh** : estimation des émissions de la production d'électricité en France |

**Champs présents uniquement dans `eco2mix-national-tr` :** `eolien_terrestre`, `eolien_offshore`, `stockage_batterie` (≤ 0, charge), `destockage_batterie` (≥ 0, décharge).

**Types incohérents entre les deux jeux :**

| Champ | `cons-def` | `tr` |
|---|---|---|
| `gaz_cogen` | text | int |
| `ech_comm_allemagne_belgique` | text | int |
| `hydraulique_fil_eau_eclusee` | int | text |

**Conclusion :** les types déclarés par l'API ne sont pas fiables. La couche staging convertira **explicitement** chaque mesure en numérique, quel que soit le type d'origine, et contrôlera les valeurs non convertibles (voir § 7, Q2).

## 4. Natures, cycle de vie et couverture

| Nature | Jeu | Du | Au | Lignes (total du jeu) |
|---|---|---|---|---|
| Données définitives | `cons-def` | 01/01/2012 00:00 | 31/12/2025 23:45 | 490 944 |
| Données consolidées | `cons-def` | 01/01/2026 00:00 | 31/08/2026 23:45 | 23 328 |
| Données temps réel | `tr` | 01/09/2026 00:00 | lendemain 23:45 (glissant) | 7 008 au 11/11/2026 |

**Raccordement :** `cons-def` se termine à `2026-08-31T21:45Z` et `tr` commence à `2026-08-31T22:00Z`. Les deux jeux sont **contigus**, sans chevauchement ni trou.

**Cycle de vie :** une même période est d'abord publiée en *temps réel*, puis *consolidée*, puis *définitive*. Elle change alors de statut **et de jeu de données**. Au 11/11/2026, les données consolidées s'arrêtent au 31/08/2026, soit un délai de consolidation observé d'environ 2,5 mois.

**Conséquences :**
- le pipeline lit les deux jeux ;
- un même instant doit pouvoir être **mis à jour** quand sa nature évolue, sans créer de doublon (RG07, RG08).

## 5. Granularité

La source publie une **grille de 15 minutes** : 96 lignes par jour local, **sans exception**, y compris les jours de changement d'heure (voir § 6). Les champs ne sont pas tous remplis à cette fréquence :

| Champs | Définitives / consolidées | Temps réel |
|---|---|---|
| Mesures (consommation, production, `taux_co2`, `ech_physiques`) | **30 min** (:00 et :30 ; NULL à :15 et :45) | **15 min** |
| Prévisions (`prevision_j1`, `prevision_j`) | 15 min | 15 min |
| Échanges commerciaux (`ech_comm_*`) | Valeur **horaire recopiée** : sur :00 et :30 jusqu'à fin juin 2024 environ, puis sur les 4 quarts d'heure | Valeur horaire recopiée sur les 4 quarts d'heure |

**Preuves (fenêtre 5 ans, `cons-def`) :** à la minute 0 : 42 216 lignes, dont 42 215 avec consommation ; à la minute 15 : 42 216 lignes, dont 0 avec consommation. Pour `tr`, la consommation est remplie à chacune des 4 minutes (1 700 lignes sur 1 728 ; l'écart correspond aux lignes futures, voir Q7).

**Exemple d'échange horaire recopié (15/06/2026, `ech_comm_angleterre`) :** 22:00, 22:15, 22:30 et 22:45 valent tous −2 933.

**Conséquences :**
- l'énergie se calcule avec la **durée réelle de l'intervalle** de chaque mesure : 0,5 h (30 min) ou 0,25 h (15 min). Un facteur fixe de 0,5 doublerait l'énergie des données temps réel ;
- les échanges commerciaux ne doivent **jamais être sommés** sur les lignes infra-horaires. Il faut d'abord les ramener à une valeur par heure ;
- observations et prévisions n'ont pas la même granularité. Elles seront séparées en staging (RG10).

## 6. Fuseaux horaires et changements d'heure

- `date_heure` est en **UTC**. `date` et `heure` sont en **heure locale de Paris**.
- En temps normal, `date` + `heure` correspond exactement à `date_heure` converti en heure de Paris.
- **Aux changements d'heure, la source force 96 lignes par jour local**, alors qu'une journée réelle compte 92 quarts d'heure (mars) ou 100 (octobre).

**Passage à l'heure d'été (dernier dimanche de mars).** L'heure locale 02:00–02:59 n'existe pas, mais la source publie quand même 4 lignes `heure` = 02:00 à 02:45. Leur `date_heure` est **identique** à celle des lignes 03:00 à 03:45 :

| `heure` | `date_heure` (UTC) | `consommation` |
|---|---|---|
| 01:30 | 2025-03-30T00:30Z | 48 415 |
| 02:00 | 2025-03-30T01:00Z | 47 832 |
| 03:00 | 2025-03-30T01:00Z | 47 832 |
| 02:30 | 2025-03-30T01:30Z | 48 415 |
| 03:30 | 2025-03-30T01:30Z | 48 397 |

Les lignes « 02:xx » sont des **lignes fantômes**, dont les valeurs sont recopiées d'autres lignes. Elles produisent **4 doublons de `date_heure` par an** : 20 sur la fenêtre (mars 2022 à 2026), tous dans `cons-def`.

**Passage à l'heure d'hiver (dernier dimanche d'octobre).** L'heure locale 02:00–02:59 existe deux fois, mais la source ne la publie qu'une fois. La **première occurrence** (de 00:00 à 00:45 UTC) est **absente** :

```text
heure 01:45 → 2025-10-25T23:45Z
heure 02:00 → 2025-10-26T01:00Z      (00:00Z à 00:45Z : aucune ligne)
```

Cela représente **4 quarts d'heure UTC manquants par an** : 16 dans `cons-def` (octobre 2022 à 2025) et 4 dans `tr` (25/10/2026). Le jeu `tr` n'a pas encore connu de passage à l'heure d'été (il commence en septembre 2026). Son comportement en mars devra être vérifié en mars 2027.

**Conséquences :**
- la référence temporelle du projet est `date_heure` (UTC) ;
- en staging, on **supprime les lignes fantômes** : ce sont celles dont `date` + `heure` ne correspond pas à `date_heure` convertie en heure de Paris ;
- l'heure manquante d'octobre est un **trou documenté**. Elle n'est ni inventée ni interpolée (RG05).

## 7. Qualité observée

Fenêtre : 168 864 lignes `cons-def` (07/11/2021 → 31/08/2026) et 7 008 lignes `tr` (01/09/2026 → 12/11/2026).

| Réf. | Constat | Jeu | Occurrences | Traitement proposé |
|---|---|---|---|---|
| Q1 | Ligne vide à la jonction définitif/consolidé : 01/01/2026 00:00, toutes les mesures à NULL | cons-def | 1 | Conserver NULL (RG05) ; test dbt avec exception documentée |
| Q2 | Valeur non numérique `"ND"` dans `gaz_cogen`, sur la même ligne que Q1 | cons-def | 1 | Conversion en NULL, tracée |
| Q3 | Types déclarés incohérents entre les jeux (§ 3) | les deux | 3 champs | Conversion explicite en staging |
| Q4 | Doublons de `date_heure` (lignes fantômes de mars, § 6) | cons-def | 20 | Suppression des lignes fantômes |
| Q5 | Heure UTC manquante (octobre, § 6) | les deux | 16 + 4 | Trou documenté |
| Q6 | Échanges commerciaux horaires recopiés sur plusieurs lignes (§ 5) | les deux | systématique | Ramener à une valeur par heure avant toute agrégation |
| Q7 | Lignes **futures** : seules les prévisions sont remplies | tr | 131 lignes le 11/11/2026 à 14:04 UTC | **Pas une anomalie.** Lignes à mettre à jour (upsert) |
| Q8 | Dernier quart d'heure pas encore publié | tr | délai d'environ 20 min | **Pas une anomalie.** Repris à l'ingestion suivante |

**Valeurs négatives légitimes (RG06), à ne pas rejeter :**

| Champ | Plage observée (MW) | Signification |
|---|---|---|
| `pompage` | −4 086 à −3 (cons-def) ; −3 441 à 0 (tr) | Consommation des pompes STEP |
| `stockage_batterie` | −487 à 0 | Charge des batteries |
| `ech_physiques` | −21 063 à +14 608 | Négatif = export |
| `ech_comm_*` | par exemple −10 173 à +11 265 (Allemagne-Belgique) | Négatif = export |

**Zéros légitimes :** `solaire` = 0 la nuit et `charbon` = 0 sont de vraies valeurs, à ne pas confondre avec NULL.

**Plages de référence (cons-def) :** consommation de 29 798 à 90 236 MW ; `taux_co2` de 5 à 111 g/kWh. Ces plages pourront servir de seuils pour des tests de vraisemblance.

## 8. Volumes et performances

| Mesure | Valeur |
|---|---|
| Lignes attendues sur 5 ans | 1 826 jours × 96 = **175 296** |
| Export d'un mois (janvier 2025) | **2 976 lignes** (= 31 × 96), **0,6 s**, environ **2,6 Mo** de JSON |
| Historique complet par exports mensuels | environ **61 appels**, moins d'une minute de transfert, environ 160 Mo de JSON |
| Même historique via `/records` | 1 753 appels de 100 lignes, et **bloqué** à 10 000 lignes par l'offset |

**Remarque :** mars et octobre 2025 comptent aussi 2 976 lignes, au lieu de 2 972 et 2 980. C'est la confirmation chiffrée du comportement décrit au § 6.

## 9. Décisions

**D1. Sources.** On utilise `eco2mix-national-cons-def` pour la période couverte par des données définitives ou consolidées, et `eco2mix-national-tr` au-delà.

**D2. Stratégie d'extraction.** L'extraction se fait par **fenêtres mensuelles** via `/exports/json`. Chaque fenêtre est un intervalle **semi-ouvert** `[début, fin[` (`>=` début et `<` fin), afin qu'aucune ligne ne soit lue deux fois à la frontière entre deux fenêtres.
*Justification :* 61 appels pour 5 ans au lieu de 1 753 ; aucune limite de 10 000 ; le mois constitue une unité naturelle de chargement, de reprise et de réingestion (§ 11.1 du cahier des charges, RG08).

**Propositions validées lors de la conception de la couche RAW (14/11/2026, voir `docs/architecture.md`) :**

- **P1. Stockage RAW.** Conserver chaque ligne telle que reçue (JSON brut), accompagnée de colonnes techniques : jeu source, fenêtre extraite, identifiant de lot, date d'ingestion. Clé d'unicité RAW proposée : `(jeu, date, heure)`. Ce couple est unique dans chaque jeu (96 heures locales distinctes par jour), alors que `date_heure` ne l'est pas (Q4).
- **P2. Clé métier analytique.** `date_heure` (UTC) + `perimetre`, après suppression des lignes fantômes. `nature` est un **attribut**, pas un élément de la clé. Quand plusieurs versions d'un même instant existent, la priorité est : définitive > consolidée > temps réel.
- **P3. Ingestion quotidienne.** Relire chaque jour l'intégralité de `tr` (un seul export, environ 7 000 lignes) et les 12 derniers mois de `cons-def` (12 exports, moins de 10 s). Cela permet de capter les consolidations et les corrections pour un coût négligeable.

## 10. Écarts avec le cahier des charges

Ces écarts ont été intégrés dans la version 1.1 de `docs/specifications.md`.

| § cahier | Hypothèse initiale | Constat | Mise à jour |
|---|---|---|---|
| 2, 5.4 | Granularité de 30 minutes | Grille de 15 min ; mesures à 30 min (définitif/consolidé) ou 15 min (temps réel) | Granularité précisée par nature |
| 5.1 | Jeu de données à confirmer | Deux jeux nécessaires | D1 |
| 5.4 | `énergie = puissance × 0,5` | Facteur dépendant de l'intervalle | `× durée de l'intervalle` (0,5 h ou 0,25 h) |
| 5.4 | Unité carbone à confirmer | `taux_co2` en g/kWh | Unité documentée |
| 8.1 | Clé incluant la nature de publication | La nature évolue dans le temps pour un même instant | P2 |
| 8.2 | Journées de 92 ou 100 quarts d'heure | La source publie toujours 96 lignes : lignes fantômes en mars, heure manquante en octobre | Règles de traitement ajoutées |
| 11.1 | Taille des lots à décider | Exports mensuels | D2 |
| — | Non prévu | Types incohérents, valeur `"ND"`, échanges horaires recopiés, champs propres à `tr` | Nouvelles règles RG13 à RG15 |

## 11. Licence et attribution

Les deux jeux sont publiés sous **Licence Ouverte v2.0 (Etalab)** :
<https://www.etalab.gouv.fr/wp-content/uploads/2017/04/ETALAB-Licence-Ouverte-v2.0.pdf>

La réutilisation est libre, y compris à des fins commerciales, à condition de **mentionner la paternité** : la source et la date de dernière mise à jour. Mention à reprendre dans le README et le tableau de bord Power BI :

> Source : RTE — éCO2mix, données publiées sur ODRÉ (odre.opendatasoft.com), Licence Ouverte v2.0. Dernière mise à jour : *date de la dernière ingestion*.

## 12. Notes d'implémentation

- **Fuseaux horaires sous Windows :** le module standard `zoneinfo` ne trouve pas `Europe/Paris` sans le paquet **`tzdata`**, à ajouter à `requirements.txt` (`ZoneInfoNotFoundError` sinon).
- **Bornes de dates :** toujours avec un décalage explicite (`+01:00`, `+02:00` ou `Z`), jamais de date « nue ».
- **Lecture des mesures :** ne pas se fier au type JSON reçu (`"1334"` contre `1334`). Les valeurs sont stockées telles quelles en RAW et converties en staging.

## 13. Questions ouvertes

1. Comportement de `tr` lors du passage à l'heure d'été (à vérifier en mars 2027).
2. Date exacte du passage des échanges commerciaux à 4 valeurs par heure (vers fin juin 2024).
3. Fréquence exacte de la bascule temps réel → consolidé (mensuelle ?), à observer pour affiner P3.
4. Les mesures sont-elles des **moyennes** sur l'intervalle ou des valeurs **instantanées** ? La réponse conditionne la validité du calcul d'énergie. À confirmer dans la documentation éCO2mix de RTE.
