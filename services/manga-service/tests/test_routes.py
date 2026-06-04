from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app
from app.routes import get_at_home_client, get_repository
from app.schemas import ChapterPageItem, ChapterPagesResponse


class FakeRepository:
    def list_manga(self, **kwargs):
        return (
            [
                {
                    "manga_id": "mangadex:manga:1",
                    "source_manga_id": "1",
                    "primary_title": "Example Manga",
                    "primary_title_language": "en",
                    "original_language": "ja",
                    "status": "ongoing",
                    "year": 2024,
                    "content_rating": "safe",
                    "publication_demographic": "shounen",
                    "tag_names": ["Action"],
                    "author_names": ["Author"],
                    "cover_file_name": "cover.jpg",
                    "cover_url": "https://uploads.mangadex.org/covers/1/cover.jpg",
                    "latest_uploaded_chapter": "chapter-1",
                    "created_at": None,
                    "updated_at": None,
                }
            ],
            1,
        )

    def get_manga_detail(self, manga_id: str):
        if manga_id == "missing":
            return None
        return {
            "manga_id": manga_id,
            "source_manga_id": "1",
            "primary_title": "Example Manga",
            "primary_title_language": "en",
            "alt_titles": [{"ja": "Example"}],
            "description": {"en": "Description"},
            "original_language": "ja",
            "available_translated_languages": ["en"],
            "status": "ongoing",
            "year": 2024,
            "content_rating": "safe",
            "publication_demographic": "shounen",
            "tag_names": ["Action"],
            "author_names": ["Author"],
            "artist_names": ["Artist"],
            "cover_file_name": "cover.jpg",
            "cover_url": "https://uploads.mangadex.org/covers/1/cover.jpg",
            "created_at": None,
            "updated_at": None,
        }

    def list_chapters_for_manga(self, **kwargs):
        return (
            [
                {
                    "chapter_id": "mangadex:chapter:1",
                    "source_chapter_id": "1",
                    "source_manga_id": "1",
                    "manga_id": kwargs["manga_id"],
                    "manga_title": "Example Manga",
                    "title": "Chapter 1",
                    "volume": "1",
                    "chapter_number": "1",
                    "translated_language": "en",
                    "pages": 24,
                    "scanlation_group_names": ["Group"],
                    "publish_at": None,
                    "readable_at": None,
                    "created_at": None,
                    "updated_at": None,
                }
            ],
            1,
        )

    def list_latest_chapters(self, **kwargs):
        return (
            [
                {
                    "chapter_id": "mangadex:chapter:1",
                    "source_chapter_id": "1",
                    "source_manga_id": "1",
                    "manga_id": "mangadex:manga:1",
                    "manga_title": "Example Manga",
                    "cover_file_name": "cover.jpg",
                    "cover_url": "https://uploads.mangadex.org/covers/1/cover.jpg",
                    "title": "Chapter 1",
                    "chapter_number": "1",
                    "translated_language": "en",
                    "pages": 24,
                    "publish_at": None,
                    "readable_at": None,
                }
            ],
            1,
        )


class FakeAtHomeClient:
    def get_chapter_pages(self, source_chapter_id: str, quality: str):
        folder = "data-saver" if quality == "data_saver" else "data"
        return ChapterPagesResponse(
            source_chapter_id=source_chapter_id,
            quality=quality,
            base_url="https://uploads.mangadex.org",
            hash="hash",
            pages=[
                ChapterPageItem(
                    page_index=1,
                    file_name="page.jpg",
                    image_url=f"https://uploads.mangadex.org/{folder}/hash/page.jpg",
                )
            ],
        )


def override_repository() -> FakeRepository:
    return FakeRepository()


def override_at_home_client() -> FakeAtHomeClient:
    return FakeAtHomeClient()


def client() -> TestClient:
    app.dependency_overrides[get_repository] = override_repository
    app.dependency_overrides[get_at_home_client] = override_at_home_client
    return TestClient(app)


def teardown_function() -> None:
    app.dependency_overrides.clear()


def test_list_manga_returns_paginated_items() -> None:
    response = client().get("/manga?limit=10&offset=0")

    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 1
    assert body["limit"] == 10
    assert body["offset"] == 0
    assert body["items"][0]["primary_title"] == "Example Manga"
    assert body["items"][0]["cover_url"] == "https://uploads.mangadex.org/covers/1/cover.jpg"


def test_get_manga_detail_returns_404_for_missing_manga() -> None:
    response = client().get("/manga/missing")

    assert response.status_code == 404


def test_get_manga_detail_returns_item() -> None:
    response = client().get("/manga/mangadex:manga:1")

    assert response.status_code == 200
    assert response.json()["manga_id"] == "mangadex:manga:1"
    assert response.json()["cover_url"] == "https://uploads.mangadex.org/covers/1/cover.jpg"


def test_list_chapters_for_manga_returns_paginated_items() -> None:
    response = client().get("/manga/mangadex:manga:1/chapters?translated_language=en")

    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 1
    assert body["items"][0]["translated_language"] == "en"


def test_latest_chapters_returns_paginated_items() -> None:
    response = client().get("/chapters/latest?limit=10")

    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 1
    assert body["items"][0]["chapter_id"] == "mangadex:chapter:1"
    assert body["items"][0]["cover_url"] == "https://uploads.mangadex.org/covers/1/cover.jpg"


def test_invalid_limit_returns_validation_error() -> None:
    response = client().get("/manga?limit=101")

    assert response.status_code == 422


def test_get_chapter_pages_returns_image_urls() -> None:
    response = client().get("/chapters/chapter-1/pages?quality=full")

    assert response.status_code == 200
    body = response.json()
    assert body["source_chapter_id"] == "chapter-1"
    assert body["quality"] == "full"
    assert body["pages"][0]["image_url"] == "https://uploads.mangadex.org/data/hash/page.jpg"


def test_invalid_chapter_page_quality_returns_validation_error() -> None:
    response = client().get("/chapters/chapter-1/pages?quality=tiny")

    assert response.status_code == 422
