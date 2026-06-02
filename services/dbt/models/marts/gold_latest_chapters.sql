with cover as (
    select distinct on (mc.source_manga_id)
        mc.source_manga_id,
        c.file_name as cover_file_name
    from {{ ref('stg_manga_cover') }} mc
    join {{ ref('stg_cover') }} c on c.source_cover_id = mc.source_cover_id
    order by mc.source_manga_id, c.updated_at desc nulls last
)
select
    c.chapter_id,
    c.source_chapter_id,
    c.source_manga_id,
    c.manga_id,
    c.manga_title,
    cover.cover_file_name,
    c.title,
    c.chapter_number,
    c.translated_language,
    c.pages,
    c.publish_at,
    c.readable_at
from {{ ref('gold_chapter_list') }} c
left join cover on cover.source_manga_id = c.source_manga_id
order by c.readable_at desc nulls last, c.publish_at desc nulls last
