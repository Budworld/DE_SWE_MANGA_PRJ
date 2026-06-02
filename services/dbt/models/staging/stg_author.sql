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
from {{ source('silver', 'author') }}
