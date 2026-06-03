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
