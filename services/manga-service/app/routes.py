from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from psycopg import Connection

from app.config import get_settings
from app.db import get_connection
from app.repositories import MangaRepository
from app.schemas import (
    ChapterListItem,
    HealthResponse,
    LatestChapterItem,
    MangaCatalogItem,
    MangaDetail,
    PaginatedResponse,
)


router = APIRouter()


def get_repository(connection: Annotated[Connection, Depends(get_connection)]) -> MangaRepository:
    return MangaRepository(connection)


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", service=get_settings().app_name)


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
