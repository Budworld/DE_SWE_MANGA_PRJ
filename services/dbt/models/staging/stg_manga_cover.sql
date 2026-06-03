select
    record->>'source_manga_id' as source_manga_id,
    record->>'source_cover_id' as source_cover_id,
    record->>'crawl_run_id' as crawl_run_id
from {{ source('silver', 'manga_cover') }}
