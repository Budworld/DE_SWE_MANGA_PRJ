from __future__ import annotations

from collections.abc import Iterator

import psycopg
from psycopg.rows import dict_row

from app.config import get_settings


def get_connection() -> Iterator[psycopg.Connection]:
    connection = psycopg.connect(get_settings().database_url, row_factory=dict_row)
    try:
        yield connection
    finally:
        connection.close()
