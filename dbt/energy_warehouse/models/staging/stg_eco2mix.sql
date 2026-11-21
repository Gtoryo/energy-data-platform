{% set mesures = [
    'consommation', 'prevision_j1', 'prevision_j',
    'nucleaire', 'eolien', 'solaire', 'hydraulique',
    'gaz', 'charbon', 'fioul', 'bioenergies',
    'eolien_terrestre', 'eolien_offshore',
    'fioul_tac', 'fioul_cogen', 'fioul_autres',
    'gaz_tac', 'gaz_cogen', 'gaz_ccg', 'gaz_autres',
    'hydraulique_fil_eau_eclusee', 'hydraulique_lacs',
    'hydraulique_step_turbinage',
    'bioenergies_dechets', 'bioenergies_biomasse', 'bioenergies_biogaz',
    'pompage', 'stockage_batterie', 'destockage_batterie',
    'ech_physiques',
    'ech_comm_angleterre', 'ech_comm_espagne', 'ech_comm_italie',
    'ech_comm_suisse', 'ech_comm_allemagne_belgique',
    'taux_co2',
] %}

select
    jeu,
    date_locale,
    heure_locale,
    (payload ->> 'date_heure')::timestamptz as date_heure,
    payload ->> 'nature' as nature,
    case payload ->> 'nature'
        when 'Données définitives' then 1
        when 'Données consolidées' then 2
        when 'Données temps réel' then 3
    end as rang_nature,
    (date_locale + heure_locale)
        <> ((payload ->> 'date_heure')::timestamptz at time zone 'Europe/Paris')
        as est_fantome,
    payload ->> 'perimetre' as perimetre,
    {% for mesure in mesures %}
    case
        when pg_input_is_valid(payload ->> '{{ mesure }}', 'numeric')
            then (payload ->> '{{ mesure }}')::numeric
    end as {{ mesure }},
    {% endfor %}
    lot_id
from {{ source('raw', 'eco2mix_national') }}
