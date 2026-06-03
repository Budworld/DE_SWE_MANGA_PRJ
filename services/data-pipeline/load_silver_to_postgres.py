from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SOURCE_TABLES = (
    "manga",
    "chapter",
    "cover",
    "author",
    "tag",
    "scanlation_group",
    "manga_author",
    "manga_artist",
    "manga_tag",
    "manga_cover",
    "chapter_manga",
    "chapter_scanlation_group",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def import_psycopg():
    try:
        import psycopg
        from psycopg.types.json import Jsonb
    except ImportError as error:
        raise SystemExit(
            "Missing dependency psycopg. Install it with:\n"
            "  pip install -r services/data-pipeline/requirements.txt"
        ) from error
    return psycopg, Jsonb


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []

    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as error:
                raise ValueError(f"Invalid JSONL at {path}:{line_number}: {error}") from error
    return records


def connection_string(args: argparse.Namespace) -> str:
    return (
        args.database_url
        or os.getenv("DATABASE_URL")
        or "postgresql://web_manga:web_manga@localhost:5432/web_manga"
    )


def ensure_schema_and_tables(conn: Any, schema: str) -> None:
    table_names = ", ".join(SOURCE_TABLES)
    with conn.cursor() as cur:
        cur.execute(f'CREATE SCHEMA IF NOT EXISTS "{schema}"')
        for table in SOURCE_TABLES:
            cur.execute(
                f'''
                CREATE TABLE IF NOT EXISTS "{schema}"."{table}" (
                    id BIGSERIAL PRIMARY KEY,
                    source TEXT NOT NULL,
                    crawl_run_id TEXT NOT NULL,
                    loaded_at TIMESTAMPTZ NOT NULL,
                    record JSONB NOT NULL
                )
                '''
            )
            cur.execute(
                f'CREATE INDEX IF NOT EXISTS "idx_{schema}_{table}_crawl_run_id" '
                f'ON "{schema}"."{table}" (crawl_run_id)'
            )
        cur.execute(
            f'''
            CREATE TABLE IF NOT EXISTS "{schema}"."_load_audit" (
                load_id TEXT PRIMARY KEY,
                source TEXT NOT NULL,
                crawl_run_id TEXT NOT NULL,
                silver_run_dir TEXT NOT NULL,
                loaded_at TIMESTAMPTZ NOT NULL,
                table_counts JSONB NOT NULL
            )
            '''
        )
    conn.commit()
    print(f"Ensured schema {schema} and tables: {table_names}")


def truncate_crawl_run(conn: Any, schema: str, crawl_run_id: str) -> None:
    with conn.cursor() as cur:
        for table in SOURCE_TABLES:
            cur.execute(f'DELETE FROM "{schema}"."{table}" WHERE crawl_run_id = %s', (crawl_run_id,))
        cur.execute(f'DELETE FROM "{schema}"."_load_audit" WHERE crawl_run_id = %s', (crawl_run_id,))
    conn.commit()


def infer_crawl_run_id(silver_run_dir: Path) -> str:
    if silver_run_dir.name.startswith("crawl_run_id="):
        return silver_run_dir.name.split("=", 1)[1]

    summary_file = silver_run_dir / "transform_summary.json"
    if summary_file.exists():
        return json.loads(summary_file.read_text(encoding="utf-8"))["crawl_run_id"]

    raise ValueError(f"Cannot infer crawl_run_id from {silver_run_dir}")


def load_table(conn: Any, Jsonb: Any, schema: str, table: str, records: list[dict[str, Any]], loaded_at: str) -> int:
    if not records:
        return 0

    rows = [
        (
            record.get("source", "mangadex"),
            record.get("crawl_run_id"),
            loaded_at,
            Jsonb(record),
        )
        for record in records
    ]

    with conn.cursor() as cur:
        cur.executemany(
            f'INSERT INTO "{schema}"."{table}" (source, crawl_run_id, loaded_at, record) VALUES (%s, %s, %s, %s)',
            rows,
        )
    conn.commit()
    return len(rows)


def load_silver_run(args: argparse.Namespace) -> dict[str, Any]:
    psycopg, Jsonb = import_psycopg()
    silver_run_dir = Path(args.silver_run_dir)
    crawl_run_id = infer_crawl_run_id(silver_run_dir)
    loaded_at = utc_now()

    with psycopg.connect(connection_string(args)) as conn:
        ensure_schema_and_tables(conn, args.schema)
        if args.overwrite:
            truncate_crawl_run(conn, args.schema, crawl_run_id)

        table_counts: dict[str, int] = {}
        for table in SOURCE_TABLES:
            records = read_jsonl(silver_run_dir / f"{table}.jsonl")
            table_counts[table] = load_table(conn, Jsonb, args.schema, table, records, loaded_at)

        load_id = f"{args.schema}:{crawl_run_id}:{loaded_at}"
        with conn.cursor() as cur:
            cur.execute(
                f'''
                INSERT INTO "{args.schema}"."_load_audit"
                    (load_id, source, crawl_run_id, silver_run_dir, loaded_at, table_counts)
                VALUES (%s, %s, %s, %s, %s, %s)
                ''',
                (load_id, "mangadex", crawl_run_id, str(silver_run_dir), loaded_at, Jsonb(table_counts)),
            )
        conn.commit()

    return {
        "source": "mangadex",
        "crawl_run_id": crawl_run_id,
        "schema": args.schema,
        "silver_run_dir": str(silver_run_dir),
        "loaded_at": loaded_at,
        "table_counts": table_counts,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Load Silver JSONL files into PostgreSQL.")
    parser.add_argument("--silver-run-dir", required=True, help="Path to data/silver/mangadex/crawl_run_id=<id>.")
    parser.add_argument("--database-url", default=None, help="PostgreSQL connection URL. Defaults to DATABASE_URL env or local docker compose URL.")
    parser.add_argument("--schema", default="silver", help="Target PostgreSQL schema.")
    parser.add_argument("--overwrite", action="store_true", help="Delete existing records for this crawl run before loading.")
    args = parser.parse_args()

    print(json.dumps(load_silver_run(args), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
