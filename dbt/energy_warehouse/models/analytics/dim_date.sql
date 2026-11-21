with bornes as (
    select
        make_date(extract(year from min(date_locale))::int, 1, 1) as premier_jour,
        make_date(extract(year from max(date_locale))::int, 12, 31) as dernier_jour
    from {{ ref('stg_eco2mix_instants') }}
),

jours as (
    select premier_jour + n as date
    from bornes
    cross join lateral generate_series(0, dernier_jour - premier_jour) as n
)

select
    date,
    extract(year from date)::int as annee,
    extract(quarter from date)::int as trimestre,
    extract(month from date)::int as mois,
    (array[
        'Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
        'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre'
    ])[extract(month from date)::int] as nom_mois,
    extract(isodow from date)::int as jour_semaine,
    (array[
        'Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche'
    ])[extract(isodow from date)::int] as nom_jour,
    extract(isodow from date) in (6, 7) as est_weekend,
    case
        when extract(month from date) in (12, 1, 2) then 'Hiver'
        when extract(month from date) in (3, 4, 5) then 'Printemps'
        when extract(month from date) in (6, 7, 8) then 'Été'
        else 'Automne'
    end as saison
from jours
