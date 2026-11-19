with mesures as (
    select
        *,
        case when rang_nature = 3 then 0.25 else 0.5 end as duree_h
    from {{ ref('stg_eco2mix_instants') }}
    where consommation is not null
)

select
    date_heure,
    date_locale as date,
    heure_locale as heure,
    nature,
    duree_h,
    consommation as consommation_mw,
    consommation * duree_h as consommation_mwh,
    prevision_j1 as prevision_j1_mw,
    prevision_j as prevision_j_mw,
    taux_co2 as taux_co2_g_par_kwh
from mesures
