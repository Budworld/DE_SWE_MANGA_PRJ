with ranked as (
    select
        record,
        row_number() over (
            partition by record->>'tag_id'
            order by loaded_at desc, id desc
        ) as row_number
    from {{ source('silver', 'tag') }}
)

select
    record->>'tag_id' as tag_id,
    record->>'source_tag_id' as source_tag_id,
    record->'name' as name,
    record->'description' as description,
    record->>'group_name' as group_name,
    nullif(record->>'version', '')::int as version,
    record->>'crawl_run_id' as crawl_run_id
from ranked
where row_number = 1
