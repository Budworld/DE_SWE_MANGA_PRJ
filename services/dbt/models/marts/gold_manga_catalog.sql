with author_names as (
    select
        ma.source_manga_id,
        jsonb_agg(distinct a.name) filter (where a.name is not null) as author_names
    from {{ ref('stg_manga_author') }} ma
    join {{ ref('stg_author') }} a on a.source_author_id = ma.source_author_id
    group by ma.source_manga_id
),
tag_names as (
    select
        mt.source_manga_id,
        jsonb_agg(distinct t.name->>'en') filter (where t.name ? 'en') as tag_names
    from {{ ref('stg_manga_tag') }} mt
    join {{ ref('stg_tag') }} t on t.source_tag_id = mt.source_tag_id
    group by mt.source_manga_id
),
cover as (
    select distinct on (mc.source_manga_id)
        mc.source_manga_id,
        c.file_name as cover_file_name
    from {{ ref('stg_manga_cover') }} mc
    join {{ ref('stg_cover') }} c on c.source_cover_id = mc.source_cover_id
    order by mc.source_manga_id, c.updated_at desc nulls last
)
select
    m.manga_id,
    m.source_manga_id,
    m.primary_title,
    m.primary_title_language,
    m.original_language,
    m.status,
    m.year,
    m.content_rating,
    m.publication_demographic,
    coalesce(t.tag_names, '[]'::jsonb) as tag_names,
    coalesce(a.author_names, '[]'::jsonb) as author_names,
    c.cover_file_name,
    m.latest_uploaded_chapter,
    m.created_at,
    m.updated_at
from {{ ref('stg_manga') }} m
left join author_names a on a.source_manga_id = m.source_manga_id
left join tag_names t on t.source_manga_id = m.source_manga_id
left join cover c on c.source_manga_id = m.source_manga_id
