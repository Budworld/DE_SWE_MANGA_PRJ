with ranked as (
    select
        record,
        row_number() over (
            partition by record->>'cover_id'
            order by loaded_at desc, id desc
        ) as row_number
    from {{ source('silver', 'cover') }}
)

select
    record->>'cover_id' as cover_id,
    record->>'source_cover_id' as source_cover_id,
    record->>'source_manga_id' as source_manga_id,
    record->>'volume' as volume,
    record->>'file_name' as file_name,
    record->>'description' as description,
    record->>'locale' as locale,
    nullif(record->>'created_at', '')::timestamptz as created_at,
    nullif(record->>'updated_at', '')::timestamptz as updated_at,
    record->>'crawl_run_id' as crawl_run_id
from ranked
where row_number = 1
