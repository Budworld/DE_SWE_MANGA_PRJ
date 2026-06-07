with ranked as (
    select
        record,
        row_number() over (
            partition by record->>'source_manga_id', record->>'source_tag_id'
            order by loaded_at desc, id desc
        ) as row_number
    from {{ source('silver', 'manga_tag') }}
)

select
    record->>'source_manga_id' as source_manga_id,
    record->>'source_tag_id' as source_tag_id,
    record->>'crawl_run_id' as crawl_run_id
from ranked
where row_number = 1
