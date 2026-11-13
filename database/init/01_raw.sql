-- =====================================================================
-- Couche RAW : copie fidèle des données reçues de l'API éCO2mix.
-- Exécution automatiquement par PostgreSQL à l'initialisation du volume.
-- Voir docs/api_study.md (9, proposition P1 à P3)
-- =====================================================================

CREATE SCHEMA IF NOT EXISTS raw;

-- Carnet de bord : une ligne par chargement (un jeu, une fenêtre).
CREATE TABLE IF NOT EXISTS raw.lots_ingestion (
    lot_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    jeu text NOT NULL,
    fenetre_debut timestamptz NOT NULL,
    fenetre_fin timestamptz NOT NULL,
    statut text NOT NULL DEFAULT 'en_cours',
    demarre_le timestamptz NOT NULL DEFAULT now(),
    termine_le timestamptz,
    nb_lignes_recues integer,
    nb_lignes_inserees integer,
    nb_lignes_modifiees integer,
    message_erreur  text,
    CONSTRAINT lots_ingestion_statut_check
        CHECK (statut IN ('en_cours', 'succes', 'echec')),
    CONSTRAINT lots_ingestion_fenetre_check
        CHECK (fenetre_debut < fenetre_fin)
);

-- Données : un enregistement de la source, dans sa dernière version reçue.
CREATE TABLE IF NOT EXISTS raw.eco2mix_national (
    jeu text NOT NULL,
    date_locale date NOT NULL,
    heure_locale time NOT NULL,
    payload jsonb NOT NULL,
    lot_id bigint NOT NULL REFERENCES raw.lots_ingestion (lot_id),
    insere_le timestamptz NOT NULL DEFAULT now(),
    modifie_le timestamptz,  -- NULL tant que la ligne n'a jamais changée
    PRIMARY KEY (jeu, date_locale, heure_locale)
)
