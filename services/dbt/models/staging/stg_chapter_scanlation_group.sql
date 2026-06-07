with ranked as (
    select
        record,
        row_number() over (
            partition by record->>'source_chapter_id', record->>'source_group_id'
            order by loaded_at desc, id desc
        ) as row_number
    from {{ source('silver', 'chapter_scanlation_group') }}
)

select
    record->>'source_chapter_id' as source_chapter_id,
    record->>'source_group_id' as source_group_id,
    record->>'crawl_run_id' as crawl_run_id
from ranked
where row_number = 1
