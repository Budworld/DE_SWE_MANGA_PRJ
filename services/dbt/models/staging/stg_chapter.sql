with ranked as (
    select
        record,
        row_number() over (
            partition by record->>'chapter_id'
            order by loaded_at desc, id desc
        ) as row_number
    from {{ source('silver', 'chapter') }}
)

select
    record->>'chapter_id' as chapter_id,
    record->>'source_chapter_id' as source_chapter_id,
    record->>'source_manga_id' as source_manga_id,
    record->>'title' as title,
    record->>'volume' as volume,
    record->>'chapter_number' as chapter_number,
    record->>'translated_language' as translated_language,
    record->>'external_url' as external_url,
    nullif(record->>'pages', '')::int as pages,
    nullif(record->>'version', '')::int as version,
    nullif(record->>'publish_at', '')::timestamptz as publish_at,
    nullif(record->>'readable_at', '')::timestamptz as readable_at,
    nullif(record->>'created_at', '')::timestamptz as created_at,
    nullif(record->>'updated_at', '')::timestamptz as updated_at,
    record->>'crawl_run_id' as crawl_run_id
from ranked
where row_number = 1
