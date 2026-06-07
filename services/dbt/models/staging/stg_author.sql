with ranked as (
    select
        record,
        row_number() over (
            partition by record->>'author_id'
            order by loaded_at desc, id desc
        ) as row_number
    from {{ source('silver', 'author') }}
)

select
    record->>'author_id' as author_id,
    record->>'source_author_id' as source_author_id,
    record->>'name' as name,
    record->'biography' as biography,
    record->>'image_url' as image_url,
    record->>'website' as website,
    record->>'twitter' as twitter,
    record->>'pixiv' as pixiv,
    nullif(record->>'created_at', '')::timestamptz as created_at,
    nullif(record->>'updated_at', '')::timestamptz as updated_at,
    record->>'crawl_run_id' as crawl_run_id
from ranked
where row_number = 1
