select
    record->>'tag_id' as tag_id,
    record->>'source_tag_id' as source_tag_id,
    record->'name' as name,
    record->'description' as description,
    record->>'group_name' as group_name,
    nullif(record->>'version', '')::int as version,
    record->>'crawl_run_id' as crawl_run_id
from {{ source('silver', 'tag') }}
