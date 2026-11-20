select distinct on (date_heure)
    *,
    case when rang_nature = 3 then 0.25 else 0.5 end as duree_h
from {{ ref('stg_eco2mix') }}
where not est_fantome
order by date_heure, rang_nature
