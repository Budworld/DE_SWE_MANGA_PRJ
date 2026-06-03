from __future__ import annotations

from datetime import datetime
from typing import Generic, TypeVar

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
    title: str | None = None
    chapter_number: str | None = None
    translated_language: str | None = None
    pages: int | None = None
    publish_at: datetime | None = None
    readable_at: datetime | None = None
