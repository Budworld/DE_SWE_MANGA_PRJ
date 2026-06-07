with ranked as (
    select
        record,
        row_number() over (
            partition by record->>'manga_id'
            order by loaded_at desc, id desc
        ) as row_number
    from {{ source('silver', 'manga') }}
)

select
    record->>'manga_id' as manga_id,
    record->>'source_manga_id' as source_manga_id,
    record->>'primary_title' as primary_title,
    record->>'primary_title_language' as primary_title_language,
    record->'alt_titles' as alt_titles,
    record->'description' as description,
    record->>'original_language' as original_language,
    record->'available_translated_languages' as available_translated_languages,
    record->>'publication_demographic' as publication_demographic,
    record->>'status' as status,
    nullif(record->>'year', '')::int as year,
    record->>'content_rating' as content_rating,
    record->>'latest_uploaded_chapter' as latest_uploaded_chapter,
    nullif(record->>'created_at', '')::timestamptz as created_at,
    nullif(record->>'updated_at', '')::timestamptz as updated_at,
    record->>'crawl_run_id' as crawl_run_id
from ranked
where row_number = 1
