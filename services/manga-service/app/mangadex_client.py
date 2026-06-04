from __future__ import annotations

import json
from typing import Literal
import urllib.request

from app.schemas import ChapterPageItem, ChapterPagesResponse


MANGADEX_API_BASE_URL = "https://api.mangadex.org"


class MangaDexAtHomeClient:
    def __init__(self, base_url: str = MANGADEX_API_BASE_URL, timeout_seconds: float = 15.0):
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    def get_chapter_pages(
        self,
        source_chapter_id: str,
        quality: Literal["data_saver", "full"],
    ) -> ChapterPagesResponse:
        request = urllib.request.Request(
            f"{self.base_url}/at-home/server/{source_chapter_id}",
            headers={"Accept": "application/json", "User-Agent": "web-manga-reader-preview/0.1"},
        )
        with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
            payload = json.loads(response.read().decode("utf-8"))

        chapter = payload["chapter"]
        base_url = payload["baseUrl"]
        chapter_hash = chapter["hash"]
        folder = "data-saver" if quality == "data_saver" else "data"
        file_names = chapter["dataSaver"] if quality == "data_saver" else chapter["data"]

        pages = [
            ChapterPageItem(
                page_index=index + 1,
                file_name=file_name,
                image_url=f"{base_url}/{folder}/{chapter_hash}/{file_name}",
            )
            for index, file_name in enumerate(file_names)
        ]

        return ChapterPagesResponse(
            source_chapter_id=source_chapter_id,
            quality=quality,
            base_url=base_url,
            hash=chapter_hash,
            pages=pages,
        )
