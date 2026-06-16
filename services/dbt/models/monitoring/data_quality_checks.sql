with checks as (
    select
        'gold_manga_catalog_not_empty' as check_name,
        count(*)::bigint as metric_value,
        1::bigint as warning_threshold,
        'fail' as failure_status
    from {{ ref('gold_manga_catalog') }}

    union all

    select
        'gold_chapter_list_not_empty' as check_name,
        count(*)::bigint as metric_value,
        1::bigint as warning_threshold,
        'fail' as failure_status
    from {{ ref('gold_chapter_list') }}

    union all

    select
        'duplicate_gold_manga_ids' as check_name,
        count(*)::bigint as metric_value,
        0::bigint as warning_threshold,
        'fail' as failure_status
    from (
        select manga_id
        from {{ ref('gold_manga_catalog') }}
        group by manga_id
        having count(*) > 1
    ) duplicate_manga

    union all

    select
        'duplicate_gold_chapter_ids' as check_name,
        count(*)::bigint as metric_value,
        0::bigint as warning_threshold,
        'fail' as failure_status
    from (
        select chapter_id
        from {{ ref('gold_chapter_list') }}
        group by chapter_id
        having count(*) > 1
    ) duplicate_chapters

    union all

    select
        'missing_cover_file_name' as check_name,
        count(*)::bigint as metric_value,
        0::bigint as warning_threshold,
        'warn' as failure_status
    from {{ ref('gold_manga_catalog') }}
    where cover_file_name is null

    union all

    select
        'chapters_without_manga' as check_name,
        count(*)::bigint as metric_value,
        0::bigint as warning_threshold,
        'warn' as failure_status
    from {{ ref('gold_chapter_list') }}
    where manga_id is null
)
select
    check_name,
    metric_value,
    case
        when failure_status = 'fail' and check_name like '%not_empty' and metric_value < warning_threshold then 'fail'
        when failure_status = 'fail' and check_name not like '%not_empty' and metric_value > warning_threshold then 'fail'
        when failure_status = 'warn' and metric_value > warning_threshold then 'warn'
        else 'pass'
    end as status,
    case
        when check_name like '%not_empty' then 'Expected at least one row.'
        when check_name like 'duplicate%' then 'Expected zero duplicate business keys.'
        when check_name = 'missing_cover_file_name' then 'Manga without cover image metadata.'
        when check_name = 'chapters_without_manga' then 'Chapters whose manga was not captured in the current catalog batch.'
        else 'Data quality check.'
    end as description
from checks
