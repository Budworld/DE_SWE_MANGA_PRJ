from __future__ import annotations

import os
from functools import lru_cache

from pydantic import BaseModel


class Settings(BaseModel):
    database_url: str = "postgresql://web_manga:web_manga@localhost:5432/web_manga"
    app_name: str = "Manga Service"
    auth_token_secret: str = "local-dev-auth-secret"
    auth_token_ttl_seconds: int = 28800
    auth_demo_admin_username: str = "admin"
    auth_demo_admin_password: str = "admin"
    auth_demo_user_username: str = "reader"
    auth_demo_user_password: str = "reader"


@lru_cache
def get_settings() -> Settings:
    return Settings(
        database_url=os.getenv("DATABASE_URL", Settings().database_url),
        app_name=os.getenv("APP_NAME", Settings().app_name),
        auth_token_secret=os.getenv("AUTH_TOKEN_SECRET", Settings().auth_token_secret),
        auth_token_ttl_seconds=int(
            os.getenv("AUTH_TOKEN_TTL_SECONDS", str(Settings().auth_token_ttl_seconds))
        ),
        auth_demo_admin_username=os.getenv(
            "AUTH_DEMO_ADMIN_USERNAME", Settings().auth_demo_admin_username
        ),
        auth_demo_admin_password=os.getenv(
            "AUTH_DEMO_ADMIN_PASSWORD", Settings().auth_demo_admin_password
        ),
        auth_demo_user_username=os.getenv(
            "AUTH_DEMO_USER_USERNAME", Settings().auth_demo_user_username
        ),
        auth_demo_user_password=os.getenv(
            "AUTH_DEMO_USER_PASSWORD", Settings().auth_demo_user_password
        ),
    )
