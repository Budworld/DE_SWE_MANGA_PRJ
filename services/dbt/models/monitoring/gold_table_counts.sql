select 'gold_manga_catalog' as table_name, count(*)::bigint as row_count from {{ ref('gold_manga_catalog') }}
union all
select 'gold_manga_detail' as table_name, count(*)::bigint as row_count from {{ ref('gold_manga_detail') }}
union all
select 'gold_chapter_list' as table_name, count(*)::bigint as row_count from {{ ref('gold_chapter_list') }}
union all
select 'gold_latest_chapters' as table_name, count(*)::bigint as row_count from {{ ref('gold_latest_chapters') }}
