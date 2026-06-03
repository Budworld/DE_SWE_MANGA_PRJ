select
    record->>'source_chapter_id' as source_chapter_id,
    record->>'source_group_id' as source_group_id,
    record->>'crawl_run_id' as crawl_run_id
from {{ source('silver', 'chapter_scanlation_group') }}
