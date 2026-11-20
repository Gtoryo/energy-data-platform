select
    i.date_heure,
    i.date_locale as date,
    i.heure_locale as heure,
    i.nature,
    i.duree_h,
    p.filiere,
    p.production_mw,
    p.production_mw * i.duree_h as production_mwh
from {{ ref('stg_eco2mix_instants') }} as i
cross join lateral (
    values
        ('nucleaire', i.nucleaire),
        ('eolien', i.eolien),
        ('solaire', i.solaire),
        ('hydraulique', i.hydraulique),
        ('bioenergies', i.bioenergies),
        ('gaz', i.gaz),
        ('charbon', i.charbon),
        ('fioul', i.fioul)
) as p (filiere, production_mw)
where p.production_mw is not null
