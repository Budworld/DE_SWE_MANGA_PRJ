from __future__ import annotations

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from psycopg import Connection

from app.config import get_settings
from app.db import get_connection
from app.mangadex_client import MangaDexAtHomeClient
from app.repositories import MangaRepository
from app.schemas import (
    AdminHealthResponse,
    CatalogStatsResponse,
    ChapterListItem,
    ChapterPagesResponse,
    DataQualityCheckItem,
    GoldTableCountItem,
    HealthResponse,
    LatestChapterItem,
    MangaCatalogItem,
    MangaDetail,
    PaginatedResponse,
    PipelineRunItem,
    PipelineSummaryResponse,
)


router = APIRouter()


def get_repository(connection: Annotated[Connection, Depends(get_connection)]) -> MangaRepository:
    return MangaRepository(connection)


def get_at_home_client() -> MangaDexAtHomeClient:
    return MangaDexAtHomeClient()


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", service=get_settings().app_name)


@router.get("/admin/health", response_model=AdminHealthResponse)
def admin_health(repository: Annotated[MangaRepository, Depends(get_repository)]) -> AdminHealthResponse:
    row = repository.admin_health()
    return AdminHealthResponse(status="ok", service=get_settings().app_name, database=row["database"])


@router.get("/admin/pipeline/runs", response_model=list[PipelineRunItem])
def list_pipeline_runs(
    repository: Annotated[MangaRepository, Depends(get_repository)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> list[PipelineRunItem]:
    return [PipelineRunItem.model_validate(row) for row in repository.pipeline_runs(limit)]


@router.get("/admin/pipeline/summary", response_model=PipelineSummaryResponse)
def get_pipeline_summary(repository: Annotated[MangaRepository, Depends(get_repository)]) -> PipelineSummaryResponse:
    return PipelineSummaryResponse.model_validate(repository.pipeline_summary())


@router.get("/admin/data-quality", response_model=list[DataQualityCheckItem])
def get_data_quality(repository: Annotated[MangaRepository, Depends(get_repository)]) -> list[DataQualityCheckItem]:
    return [DataQualityCheckItem.model_validate(row) for row in repository.data_quality_checks()]


@router.get("/admin/catalog/stats", response_model=CatalogStatsResponse)
def get_catalog_stats(repository: Annotated[MangaRepository, Depends(get_repository)]) -> CatalogStatsResponse:
    return CatalogStatsResponse.model_validate(repository.catalog_stats())


@router.get("/admin/gold-table-counts", response_model=list[GoldTableCountItem])
def get_gold_table_counts(repository: Annotated[MangaRepository, Depends(get_repository)]) -> list[GoldTableCountItem]:
    return [GoldTableCountItem.model_validate(row) for row in repository.gold_table_counts()]


@router.get("/manga", response_model=PaginatedResponse[MangaCatalogItem])
def list_manga(
    repository: Annotated[MangaRepository, Depends(get_repository)],
    q: str | None = None,
    status: str | None = None,
    original_language: str | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> PaginatedResponse[MangaCatalogItem]:
    rows, count = repository.list_manga(
        q=q,
        status=status,
        original_language=original_language,
        limit=limit,
        offset=offset,
    )
    return PaginatedResponse(items=rows, limit=limit, offset=offset, count=count)


@router.get("/chapters/{source_chapter_id}/pages", response_model=ChapterPagesResponse)
def get_chapter_pages(
    source_chapter_id: str,
    at_home_client: Annotated[MangaDexAtHomeClient, Depends(get_at_home_client)],
    quality: Literal["data_saver", "full"] = "data_saver",
) -> ChapterPagesResponse:
    try:
        return at_home_client.get_chapter_pages(source_chapter_id=source_chapter_id, quality=quality)
    except Exception as error:
        raise HTTPException(status_code=502, detail="Failed to fetch MangaDex chapter pages") from error


@router.get("/manga/{manga_id}", response_model=MangaDetail)
def get_manga_detail(
    manga_id: str,
    repository: Annotated[MangaRepository, Depends(get_repository)],
) -> MangaDetail:
    row = repository.get_manga_detail(manga_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Manga not found")
    return MangaDetail.model_validate(row)


@router.get("/manga/{manga_id}/chapters", response_model=PaginatedResponse[ChapterListItem])
def list_chapters_for_manga(
    manga_id: str,
    repository: Annotated[MangaRepository, Depends(get_repository)],
    translated_language: str | None = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> PaginatedResponse[ChapterListItem]:
    rows, count = repository.list_chapters_for_manga(
        manga_id=manga_id,
        translated_language=translated_language,
        limit=limit,
        offset=offset,
    )
    return PaginatedResponse(items=rows, limit=limit, offset=offset, count=count)


@router.get("/chapters/latest", response_model=PaginatedResponse[LatestChapterItem])
def list_latest_chapters(
    repository: Annotated[MangaRepository, Depends(get_repository)],
    translated_language: str | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> PaginatedResponse[LatestChapterItem]:
    rows, count = repository.list_latest_chapters(
        translated_language=translated_language,
        limit=limit,
        offset=offset,
    )
    return PaginatedResponse(items=rows, limit=limit, offset=offset, count=count)
