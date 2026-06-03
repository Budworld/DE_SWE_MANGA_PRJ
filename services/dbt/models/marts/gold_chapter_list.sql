with group_names as (
    select
        csg.source_chapter_id,
        jsonb_agg(distinct sg.name) filter (where sg.name is not null) as scanlation_group_names
    from {{ ref('stg_chapter_scanlation_group') }} csg
    join {{ ref('stg_scanlation_group') }} sg on sg.source_group_id = csg.source_group_id
    group by csg.source_chapter_id
)
select
    c.chapter_id,
    c.source_chapter_id,
    c.source_manga_id,
    m.manga_id,
    m.primary_title as manga_title,
    c.title,
    c.volume,
    c.chapter_number,
    c.translated_language,
    c.pages,
    coalesce(g.scanlation_group_names, '[]'::jsonb) as scanlation_group_names,
    c.publish_at,
    c.readable_at,
    c.created_at,
    c.updated_at
from {{ ref('stg_chapter') }} c
left join {{ ref('stg_manga') }} m on m.source_manga_id = c.source_manga_id
left join group_names g on g.source_chapter_id = c.source_chapter_id
