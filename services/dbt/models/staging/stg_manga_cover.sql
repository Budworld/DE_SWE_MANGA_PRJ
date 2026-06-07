with ranked as (
    select
        record,
        row_number() over (
            partition by record->>'source_manga_id', record->>'source_cover_id'
            order by loaded_at desc, id desc
        ) as row_number
    from {{ source('silver', 'manga_cover') }}
)

select
    record->>'source_manga_id' as source_manga_id,
    record->>'source_cover_id' as source_cover_id,
    record->>'cover_file_name' as cover_file_name,
    record->>'cover_volume' as cover_volume,
    record->>'cover_locale' as cover_locale,
    record->>'crawl_run_id' as crawl_run_id
from ranked
where row_number = 1
