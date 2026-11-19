select distinct on (date_heure) *
from {{ ref('stg_eco2mix') }}
where not est_fantome
order by date_heure, rang_nature
