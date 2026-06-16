from __future__ import annotations

from datetime import datetime
from typing import Generic, Literal, TypeVar

from pydantic import BaseModel, ConfigDict, Field


T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    limit: int
    offset: int
    count: int


class HealthResponse(BaseModel):
    status: str
    service: str


class MangaCatalogItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    manga_id: str
    source_manga_id: str
    primary_title: str
    primary_title_language: str | None = None
    original_language: str | None = None
    status: str | None = None
    year: int | None = None
    content_rating: str | None = None
    publication_demographic: str | None = None
    tag_names: list[str] = Field(default_factory=list)
    author_names: list[str] = Field(default_factory=list)
    cover_file_name: str | None = None
    cover_url: str | None = None
    latest_uploaded_chapter: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class MangaDetail(BaseModel):
    manga_id: str
    source_manga_id: str
    primary_title: str
    primary_title_language: str | None = None
    alt_titles: list[dict[str, str]] = Field(default_factory=list)
    description: dict[str, str] = Field(default_factory=dict)
    original_language: str | None = None
    available_translated_languages: list[str] = Field(default_factory=list)
    status: str | None = None
    year: int | None = None
    content_rating: str | None = None
    publication_demographic: str | None = None
    tag_names: list[str] = Field(default_factory=list)
    author_names: list[str] = Field(default_factory=list)
    artist_names: list[str] = Field(default_factory=list)
    cover_file_name: str | None = None
    cover_url: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ChapterListItem(BaseModel):
    chapter_id: str
    source_chapter_id: str
    source_manga_id: str | None = None
    manga_id: str | None = None
    manga_title: str | None = None
    title: str | None = None
    volume: str | None = None
    chapter_number: str | None = None
    translated_language: str | None = None
    pages: int | None = None
    scanlation_group_names: list[str] = Field(default_factory=list)
    publish_at: datetime | None = None
    readable_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class LatestChapterItem(BaseModel):
    chapter_id: str
    source_chapter_id: str
    source_manga_id: str | None = None
    manga_id: str | None = None
    manga_title: str | None = None
    cover_file_name: str | None = None
    cover_url: str | None = None
    title: str | None = None
    chapter_number: str | None = None
    translated_language: str | None = None
    pages: int | None = None
    publish_at: datetime | None = None
    readable_at: datetime | None = None


class ChapterPageItem(BaseModel):
    page_index: int
    file_name: str
    image_url: str


class ChapterPagesResponse(BaseModel):
    source_chapter_id: str
    quality: Literal["data_saver", "full"]
    base_url: str
    hash: str
    pages: list[ChapterPageItem]


class AdminHealthResponse(BaseModel):
    status: str
    service: str
    database: str


class PipelineRunItem(BaseModel):
    crawl_run_id: str
    loaded_at: datetime | None = None
    manga_rows: int = 0
    chapter_rows: int = 0
    cover_rows: int = 0
    author_rows: int = 0
    tag_rows: int = 0
    scanlation_group_rows: int = 0


class GoldTableCountItem(BaseModel):
    table_name: str
    row_count: int


class DataQualityCheckItem(BaseModel):
    check_name: str
    status: Literal["pass", "warn", "fail"]
    metric_value: int
    description: str


class CatalogStatsResponse(BaseModel):
    manga_count: int
    chapter_count: int
    latest_chapter_count: int
    missing_cover_count: int
    chapters_without_manga_count: int
    original_language_counts: dict[str, int] = Field(default_factory=dict)
    status_counts: dict[str, int] = Field(default_factory=dict)


class PipelineSummaryResponse(BaseModel):
    latest_crawl_run_id: str | None = None
    latest_loaded_at: datetime | None = None
    silver_manga_rows: int
    silver_distinct_manga: int
    silver_chapter_rows: int
    silver_distinct_chapters: int
    gold_manga_count: int
    gold_chapter_count: int
    gold_latest_chapter_count: int
    gold_table_counts: list[GoldTableCountItem] = Field(default_factory=list)
    latest_airflow_dag_state: str | None = None
