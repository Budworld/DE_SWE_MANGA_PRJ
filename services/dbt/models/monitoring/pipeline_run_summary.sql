select
    crawl_run_id,
    max(loaded_at) as loaded_at,
    count(*) filter (where source_table = 'manga') as manga_rows,
    count(*) filter (where source_table = 'chapter') as chapter_rows,
    count(*) filter (where source_table = 'cover') as cover_rows,
    count(*) filter (where source_table = 'author') as author_rows,
    count(*) filter (where source_table = 'tag') as tag_rows,
    count(*) filter (where source_table = 'scanlation_group') as scanlation_group_rows
from (
    select crawl_run_id, loaded_at, 'manga' as source_table from {{ source('silver', 'manga') }}
    union all
    select crawl_run_id, loaded_at, 'chapter' as source_table from {{ source('silver', 'chapter') }}
    union all
    select crawl_run_id, loaded_at, 'cover' as source_table from {{ source('silver', 'cover') }}
    union all
    select crawl_run_id, loaded_at, 'author' as source_table from {{ source('silver', 'author') }}
    union all
    select crawl_run_id, loaded_at, 'tag' as source_table from {{ source('silver', 'tag') }}
    union all
    select crawl_run_id, loaded_at, 'scanlation_group' as source_table from {{ source('silver', 'scanlation_group') }}
) counts
group by crawl_run_id
