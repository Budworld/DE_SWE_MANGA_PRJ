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

    def admin_health(self):
        return {"database": "web_manga"}

    def pipeline_runs(self, limit: int):
        return [
            {
                "crawl_run_id": "run-1",
                "loaded_at": None,
                "manga_rows": 10,
                "chapter_rows": 20,
                "cover_rows": 10,
                "author_rows": 5,
                "tag_rows": 30,
                "scanlation_group_rows": 3,
            }
        ]

    def gold_table_counts(self):
        return [
            {"table_name": "gold_manga_catalog", "row_count": 10},
            {"table_name": "gold_chapter_list", "row_count": 20},
        ]

    def pipeline_summary(self):
        return {
            "latest_crawl_run_id": "run-1",
            "latest_loaded_at": None,
            "silver_manga_rows": 20,
            "silver_distinct_manga": 10,
            "silver_chapter_rows": 30,
            "silver_distinct_chapters": 20,
            "gold_manga_count": 10,
            "gold_chapter_count": 20,
            "gold_latest_chapter_count": 20,
            "gold_table_counts": self.gold_table_counts(),
            "latest_airflow_dag_state": "success",
        }

    def data_quality_checks(self):
        return [
            {
                "check_name": "duplicate_gold_manga_ids",
                "status": "pass",
                "metric_value": 0,
                "description": "Expected zero duplicate business keys.",
            },
            {
                "check_name": "missing_cover_file_name",
                "status": "warn",
                "metric_value": 2,
                "description": "Manga without cover image metadata.",
            },
        ]

    def catalog_stats(self):
        return {
            "manga_count": 10,
            "chapter_count": 20,
            "latest_chapter_count": 20,
            "missing_cover_count": 2,
            "chapters_without_manga_count": 1,
            "original_language_counts": {"ja": 8, "en": 2},
            "status_counts": {"ongoing": 7, "completed": 3},
        }


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


def admin_headers(test_client: TestClient) -> dict[str, str]:
    response = test_client.post("/auth/login", json={"username": "admin", "password": "admin"})
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def user_headers(test_client: TestClient) -> dict[str, str]:
    response = test_client.post("/auth/login", json={"username": "reader", "password": "reader"})
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


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


def test_login_returns_admin_token() -> None:
    response = client().post("/auth/login", json={"username": "admin", "password": "admin"})

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["user"] == {"username": "admin", "role": "admin"}


def test_login_rejects_invalid_credentials() -> None:
    response = client().post("/auth/login", json={"username": "admin", "password": "bad"})

    assert response.status_code == 401


def test_me_returns_current_user() -> None:
    test_client = client()
    response = test_client.get("/auth/me", headers=admin_headers(test_client))

    assert response.status_code == 200
    assert response.json() == {"username": "admin", "role": "admin"}


def test_me_requires_token() -> None:
    response = client().get("/auth/me")

    assert response.status_code == 401


def test_admin_pipeline_summary_requires_token() -> None:
    response = client().get("/admin/pipeline/summary")

    assert response.status_code == 401


def test_admin_pipeline_summary_rejects_user_role() -> None:
    test_client = client()
    response = test_client.get("/admin/pipeline/summary", headers=user_headers(test_client))

    assert response.status_code == 403


def test_admin_pipeline_summary_returns_counts() -> None:
    test_client = client()
    response = test_client.get("/admin/pipeline/summary", headers=admin_headers(test_client))

    assert response.status_code == 200
    body = response.json()
    assert body["latest_crawl_run_id"] == "run-1"
    assert body["gold_manga_count"] == 10
    assert body["latest_airflow_dag_state"] == "success"


def test_admin_pipeline_runs_returns_recent_runs() -> None:
    test_client = client()
    response = test_client.get("/admin/pipeline/runs?limit=5", headers=admin_headers(test_client))

    assert response.status_code == 200
    assert response.json()[0]["crawl_run_id"] == "run-1"


def test_admin_data_quality_returns_checks() -> None:
    test_client = client()
    response = test_client.get("/admin/data-quality", headers=admin_headers(test_client))

    assert response.status_code == 200
    body = response.json()
    assert body[0]["check_name"] == "duplicate_gold_manga_ids"
    assert body[1]["status"] == "warn"


def test_admin_catalog_stats_returns_distribution_counts() -> None:
    test_client = client()
    response = test_client.get("/admin/catalog/stats", headers=admin_headers(test_client))

    assert response.status_code == 200
    body = response.json()
    assert body["manga_count"] == 10
    assert body["original_language_counts"]["ja"] == 8
