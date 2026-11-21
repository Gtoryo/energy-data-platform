-- Un jour ne doit pas compter plus de 24 heures de mesures.
-- Renvoie les jours fautifs : une durée d'intervalle fausse les ferait apparaître.
select
    date,
    sum(duree_h) as heures
from {{ ref('fct_consommation') }}
group by date
having sum(duree_h) > 24
