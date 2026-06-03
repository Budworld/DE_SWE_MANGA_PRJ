from __future__ import annotations

import os
from functools import lru_cache

from pydantic import BaseModel


class Settings(BaseModel):
    database_url: str = "postgresql://web_manga:web_manga@localhost:5432/web_manga"
    app_name: str = "Manga Service"


@lru_cache
def get_settings() -> Settings:
    return Settings(
        database_url=os.getenv("DATABASE_URL", Settings().database_url),
        app_name=os.getenv("APP_NAME", Settings().app_name),
    )
