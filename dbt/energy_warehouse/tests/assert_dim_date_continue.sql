-- Power BI exige un calendrier sans trou, qui couvre des années entières.
-- Renvoie une ligne si ce n'est pas le cas.
select
    min(date) as premier_jour,
    max(date) as dernier_jour,
    count(*) as nb_jours
from {{ ref('dim_date') }}
having count(*) <> max(date) - min(date) + 1
    or to_char(min(date), 'MM-DD') <> '01-01'
    or to_char(max(date), 'MM-DD') <> '12-31'
