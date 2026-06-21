from __future__ import annotations

from typing import Any

from psycopg import Connection


class MangaRepository:
    def __init__(self, connection: Connection):
        self.connection = connection

    def list_manga(
        self,
        *,
        q: str | None,
        status: str | None,
        original_language: str | None,
        limit: int,
        offset: int,
    ) -> tuple[list[dict[str, Any]], int]:
        where: list[str] = []
        params: dict[str, Any] = {"limit": limit, "offset": offset}

        if q:
            where.append("primary_title ILIKE %(q)s")
            params["q"] = f"%{q}%"
        if status:
            where.append("status = %(status)s")
            params["status"] = status
        if original_language:
            where.append("original_language = %(original_language)s")
            params["original_language"] = original_language

        where_sql = f"where {' and '.join(where)}" if where else ""
        count_sql = f"select count(*) as total from gold.gold_manga_catalog {where_sql}"
        data_sql = f"""
            select
                manga_id,
                source_manga_id,
                primary_title,
                primary_title_language,
                original_language,
                status,
                year,
                content_rating,
                publication_demographic,
                coalesce(tag_names, '[]'::jsonb) as tag_names,
                coalesce(author_names, '[]'::jsonb) as author_names,
                cover_file_name,
                case
                    when source_manga_id is not null and cover_file_name is not null
                    then concat('https://uploads.mangadex.org/covers/', source_manga_id, '/', cover_file_name)
                    else null
                end as cover_url,
                latest_uploaded_chapter,
                created_at,
                updated_at
            from gold.gold_manga_catalog
            {where_sql}
            order by updated_at desc nulls last, primary_title asc
            limit %(limit)s offset %(offset)s
        """

        with self.connection.cursor() as cursor:
            cursor.execute(count_sql, params)
            total = cursor.fetchone()["total"]
            cursor.execute(data_sql, params)
            rows = cursor.fetchall()
        return rows, total

    def get_manga_detail(self, manga_id: str) -> dict[str, Any] | None:
        sql = """
            select
                manga_id,
                source_manga_id,
                primary_title,
                primary_title_language,
                coalesce(alt_titles, '[]'::jsonb) as alt_titles,
                coalesce(description, '{}'::jsonb) as description,
                original_language,
                coalesce(available_translated_languages, '[]'::jsonb) as available_translated_languages,
                status,
                year,
                content_rating,
                publication_demographic,
                coalesce(tag_names, '[]'::jsonb) as tag_names,
                coalesce(author_names, '[]'::jsonb) as author_names,
                coalesce(artist_names, '[]'::jsonb) as artist_names,
                cover_file_name,
                case
                    when source_manga_id is not null and cover_file_name is not null
                    then concat('https://uploads.mangadex.org/covers/', source_manga_id, '/', cover_file_name)
                    else null
                end as cover_url,
                created_at,
                updated_at
            from gold.gold_manga_detail
            where manga_id = %(manga_id)s
        """
        with self.connection.cursor() as cursor:
            cursor.execute(sql, {"manga_id": manga_id})
            return cursor.fetchone()

    def list_chapters_for_manga(
        self,
        *,
        manga_id: str,
        translated_language: str | None,
        limit: int,
        offset: int,
    ) -> tuple[list[dict[str, Any]], int]:
        where = ["manga_id = %(manga_id)s"]
        params: dict[str, Any] = {"manga_id": manga_id, "limit": limit, "offset": offset}

        if translated_language:
            where.append("translated_language = %(translated_language)s")
            params["translated_language"] = translated_language

        where_sql = f"where {' and '.join(where)}"
        count_sql = f"select count(*) as total from gold.gold_chapter_list {where_sql}"
        data_sql = f"""
            select
                chapter_id,
                source_chapter_id,
                source_manga_id,
                manga_id,
                manga_title,
                title,
                volume,
                chapter_number,
                translated_language,
                pages,
                coalesce(scanlation_group_names, '[]'::jsonb) as scanlation_group_names,
                publish_at,
                readable_at,
                created_at,
                updated_at
            from gold.gold_chapter_list
            {where_sql}
            order by readable_at desc nulls last, publish_at desc nulls last
            limit %(limit)s offset %(offset)s
        """

        with self.connection.cursor() as cursor:
            cursor.execute(count_sql, params)
            total = cursor.fetchone()["total"]
            cursor.execute(data_sql, params)
            rows = cursor.fetchall()
        return rows, total

    def list_latest_chapters(
        self,
        *,
        translated_language: str | None,
        limit: int,
        offset: int,
    ) -> tuple[list[dict[str, Any]], int]:
        where: list[str] = []
        params: dict[str, Any] = {"limit": limit, "offset": offset}

        if translated_language:
            where.append("translated_language = %(translated_language)s")
            params["translated_language"] = translated_language

        where_sql = f"where {' and '.join(where)}" if where else ""
        count_sql = f"select count(*) as total from gold.gold_latest_chapters {where_sql}"
        data_sql = f"""
            select
                chapter_id,
                source_chapter_id,
                source_manga_id,
                manga_id,
                manga_title,
                cover_file_name,
                case
                    when source_manga_id is not null and cover_file_name is not null
                    then concat('https://uploads.mangadex.org/covers/', source_manga_id, '/', cover_file_name)
                    else null
                end as cover_url,
                title,
                chapter_number,
                translated_language,
                pages,
                publish_at,
                readable_at
            from gold.gold_latest_chapters
            {where_sql}
            order by readable_at desc nulls last, publish_at desc nulls last
            limit %(limit)s offset %(offset)s
        """

        with self.connection.cursor() as cursor:
            cursor.execute(count_sql, params)
            total = cursor.fetchone()["total"]
            cursor.execute(data_sql, params)
            rows = cursor.fetchall()
        return rows, total

    def admin_health(self) -> dict[str, str]:
        with self.connection.cursor() as cursor:
            cursor.execute("select current_database() as database")
            row = cursor.fetchone()
        return {"database": row["database"]}

    def pipeline_runs(self, limit: int) -> list[dict[str, Any]]:
        sql = """
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
                select crawl_run_id, loaded_at, 'manga' as source_table from silver.manga
                union all
                select crawl_run_id, loaded_at, 'chapter' as source_table from silver.chapter
                union all
                select crawl_run_id, loaded_at, 'cover' as source_table from silver.cover
                union all
                select crawl_run_id, loaded_at, 'author' as source_table from silver.author
                union all
                select crawl_run_id, loaded_at, 'tag' as source_table from silver.tag
                union all
                select crawl_run_id, loaded_at, 'scanlation_group' as source_table from silver.scanlation_group
            ) counts
            group by crawl_run_id
            order by loaded_at desc nulls last, crawl_run_id desc
            limit %(limit)s
        """
        with self.connection.cursor() as cursor:
            cursor.execute(sql, {"limit": limit})
            return cursor.fetchall()

    def gold_table_counts(self) -> list[dict[str, Any]]:
        sql = """
            select 'gold_manga_catalog' as table_name, count(*)::bigint as row_count from gold.gold_manga_catalog
            union all
            select 'gold_manga_detail' as table_name, count(*)::bigint as row_count from gold.gold_manga_detail
            union all
            select 'gold_chapter_list' as table_name, count(*)::bigint as row_count from gold.gold_chapter_list
            union all
            select 'gold_latest_chapters' as table_name, count(*)::bigint as row_count from gold.gold_latest_chapters
        """
        with self.connection.cursor() as cursor:
            cursor.execute(sql)
            return cursor.fetchall()

    def pipeline_summary(self) -> dict[str, Any]:
        sql = """
            with latest_run as (
                select crawl_run_id, max(loaded_at) as loaded_at
                from silver.manga
                group by crawl_run_id
                order by loaded_at desc nulls last, crawl_run_id desc
                limit 1
            )
            select
                (select crawl_run_id from latest_run) as latest_crawl_run_id,
                (select loaded_at from latest_run) as latest_loaded_at,
                (select count(*) from silver.manga)::bigint as silver_manga_rows,
                (select count(distinct record->>'manga_id') from silver.manga)::bigint as silver_distinct_manga,
                (select count(*) from silver.chapter)::bigint as silver_chapter_rows,
                (select count(distinct record->>'chapter_id') from silver.chapter)::bigint as silver_distinct_chapters,
                (select count(*) from gold.gold_manga_catalog)::bigint as gold_manga_count,
                (select count(*) from gold.gold_chapter_list)::bigint as gold_chapter_count,
                (select count(*) from gold.gold_latest_chapters)::bigint as gold_latest_chapter_count
        """
        with self.connection.cursor() as cursor:
            cursor.execute(sql)
            row = cursor.fetchone()
            cursor.execute("select to_regclass('public.dag_run') as dag_run_table")
            if cursor.fetchone()["dag_run_table"]:
                cursor.execute(
                    """
                    select state
                    from public.dag_run
                    where dag_id = 'mangadex_data_pipeline'
                    order by execution_date desc
                    limit 1
                    """
                )
                dag_run = cursor.fetchone()
                row["latest_airflow_dag_state"] = dag_run["state"] if dag_run else None
            else:
                row["latest_airflow_dag_state"] = None
        row["gold_table_counts"] = self.gold_table_counts()
        return row

    def data_quality_checks(self) -> list[dict[str, Any]]:
        sql = """
            with checks as (
                select 'gold_manga_catalog_not_empty' as check_name, count(*)::bigint as metric_value, 'fail' as severity
                from gold.gold_manga_catalog
                union all
                select 'gold_chapter_list_not_empty' as check_name, count(*)::bigint as metric_value, 'fail' as severity
                from gold.gold_chapter_list
                union all
                select 'duplicate_gold_manga_ids' as check_name, count(*)::bigint as metric_value, 'fail' as severity
                from (
                    select manga_id from gold.gold_manga_catalog group by manga_id having count(*) > 1
                ) duplicate_manga
                union all
                select 'duplicate_gold_chapter_ids' as check_name, count(*)::bigint as metric_value, 'fail' as severity
                from (
                    select chapter_id from gold.gold_chapter_list group by chapter_id having count(*) > 1
                ) duplicate_chapters
                union all
                select 'missing_cover_file_name' as check_name, count(*)::bigint as metric_value, 'warn' as severity
                from gold.gold_manga_catalog where cover_file_name is null
                union all
                select 'chapters_without_manga' as check_name, count(*)::bigint as metric_value, 'warn' as severity
                from gold.gold_chapter_list where manga_id is null
                union all
                select
                    'chapter_manga_match_rate_percent' as check_name,
                    coalesce(round(100.0 * count(*) filter (where manga_id is not null) / nullif(count(*), 0)), 0)::bigint as metric_value,
                    'warn_min' as severity
                from gold.gold_chapter_list
                union all
                select 'manga_without_chapters' as check_name, count(*)::bigint as metric_value, 'warn' as severity
                from gold.gold_manga_catalog m
                left join gold.gold_chapter_list c on c.source_manga_id = m.source_manga_id
                where c.source_chapter_id is null
                union all
                select 'latest_chapters_missing_manga_title' as check_name, count(*)::bigint as metric_value, 'fail' as severity
                from gold.gold_latest_chapters where manga_title is null
                union all
                select 'latest_chapters_missing_cover' as check_name, count(*)::bigint as metric_value, 'warn' as severity
                from gold.gold_latest_chapters where cover_file_name is null
            )
            , results as (
                select
                    check_name,
                    metric_value,
                    case
                        when check_name like '%not_empty' and metric_value = 0 then 'fail'
                        when severity = 'fail' and check_name not like '%not_empty' and metric_value > 0 then 'fail'
                        when severity = 'warn' and metric_value > 0 then 'warn'
                        when severity = 'warn_min' and metric_value < 100 then 'warn'
                        else 'pass'
                    end as status,
                    case
                        when check_name like '%not_empty' then 'Expected at least one row.'
                        when check_name like 'duplicate%' then 'Expected zero duplicate business keys.'
                        when check_name = 'missing_cover_file_name' then 'Manga without cover image metadata.'
                        when check_name = 'chapters_without_manga' then 'Chapters whose manga was not captured in the catalog batch.'
                        when check_name = 'chapter_manga_match_rate_percent' then 'Expected every chapter to match a captured manga.'
                        when check_name = 'manga_without_chapters' then 'Expected every catalog manga to have at least one chapter.'
                        when check_name = 'latest_chapters_missing_manga_title' then 'Latest feed chapters must include manga title for the web UI.'
                        when check_name = 'latest_chapters_missing_cover' then 'Latest feed chapters should include cover metadata for thumbnail rendering.'
                        else 'Data quality check.'
                    end as description
                from checks
            )
            select check_name, metric_value, status, description
            from results
            order by
                case
                    when status = 'fail' then 1
                    when status = 'warn' then 2
                    else 3
                end,
                check_name
        """
        with self.connection.cursor() as cursor:
            cursor.execute(sql)
            return cursor.fetchall()

    def catalog_stats(self) -> dict[str, Any]:
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                select
                    (select count(*) from gold.gold_manga_catalog)::bigint as manga_count,
                    (select count(*) from gold.gold_chapter_list)::bigint as chapter_count,
                    (select count(*) from gold.gold_latest_chapters)::bigint as latest_chapter_count,
                    (select count(*) from gold.gold_manga_catalog where cover_file_name is null)::bigint as missing_cover_count,
                    (select count(*) from gold.gold_chapter_list where manga_id is null)::bigint as chapters_without_manga_count
                """
            )
            stats = cursor.fetchone()

            cursor.execute(
                """
                select coalesce(original_language, 'unknown') as key, count(*)::bigint as value
                from gold.gold_manga_catalog
                group by coalesce(original_language, 'unknown')
                order by value desc, key asc
                """
            )
            stats["original_language_counts"] = {row["key"]: row["value"] for row in cursor.fetchall()}

            cursor.execute(
                """
                select coalesce(status, 'unknown') as key, count(*)::bigint as value
                from gold.gold_manga_catalog
                group by coalesce(status, 'unknown')
                order by value desc, key asc
                """
            )
            stats["status_counts"] = {row["key"]: row["value"] for row in cursor.fetchall()}

        return stats
