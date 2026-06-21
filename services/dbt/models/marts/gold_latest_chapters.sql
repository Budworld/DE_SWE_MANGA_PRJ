select
    c.chapter_id,
    c.source_chapter_id,
    c.source_manga_id,
    m.manga_id,
    m.primary_title as manga_title,
    m.cover_file_name,
    c.title,
    c.chapter_number,
    c.translated_language,
    c.pages,
    c.publish_at,
    c.readable_at
from {{ ref('gold_chapter_list') }} c
join {{ ref('gold_manga_catalog') }} m on m.source_manga_id = c.source_manga_id
order by c.readable_at desc nulls last, c.publish_at desc nulls last
