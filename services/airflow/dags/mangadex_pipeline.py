from __future__ import annotations

import logging
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import psycopg
from airflow.decorators import dag, task
from airflow.operators.python import get_current_context


PROJECT_ROOT = Path(os.getenv("WEB_MANGA_PROJECT_ROOT", "/opt/airflow/project"))
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://web_manga:web_manga@postgres:5432/web_manga")
DBT_TARGET = os.getenv("DBT_TARGET", "dev")
SOURCE = "mangadex"
GOLD_TABLES = (
    "gold_manga_catalog",
    "gold_manga_detail",
    "gold_chapter_list",
    "gold_latest_chapters",
)


def run_project_command(command: list[str], env: dict[str, str] | None = None) -> str:
    logging.info("Running command: %s", " ".join(command))
    process_env = os.environ.copy()
    if env:
        process_env.update(env)

    result = subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        env=process_env,
        capture_output=True,
        text=True,
        check=False,
    )

    if result.stdout:
        logging.info("stdout:\n%s", result.stdout)
    if result.stderr:
        logging.warning("stderr:\n%s", result.stderr)
    if result.returncode != 0:
        raise RuntimeError(f"Command failed with exit code {result.returncode}: {' '.join(command)}")

    return result.stdout


def param_value(name: str, default: Any) -> Any:
    context = get_current_context()
    return context["params"].get(name, default)


def run_dir(layer: str, crawl_run_id: str) -> str:
    return str(PROJECT_ROOT / "data" / layer / SOURCE / f"crawl_run_id={crawl_run_id}")


def executable(name: str) -> str:
    path = shutil.which(name)
    if not path:
        raise RuntimeError(f"Required executable is not available on PATH: {name}")
    return path


def data_target_env() -> dict[str, str]:
    return {
        "DATABASE_URL": DATABASE_URL,
        "DBT_TARGET": DBT_TARGET,
        "POSTGRES_HOST": os.getenv("POSTGRES_HOST", "postgres"),
        "POSTGRES_PORT": os.getenv("POSTGRES_PORT", "5432"),
        "POSTGRES_DB": os.getenv("POSTGRES_DB", "web_manga"),
        "POSTGRES_USER": os.getenv("POSTGRES_USER", "web_manga"),
        "POSTGRES_PASSWORD": os.getenv("POSTGRES_PASSWORD", "web_manga"),
        "POSTGRES_SSLMODE": os.getenv("POSTGRES_SSLMODE", "prefer"),
    }


@dag(
    dag_id="mangadex_data_pipeline",
    description="Orchestrate MangaDex Raw -> Bronze -> Silver -> PostgreSQL -> dbt Gold.",
    schedule=None,
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["mangadex", "de", "web-manga"],
    params={
        "limit": 10,
        "pages": 1,
        "start_offset": 0,
        "pause_seconds": 0.5,
        "translated_language": "en",
    },
)
def mangadex_data_pipeline() -> None:
    @task
    def log_data_target() -> str:
        target_mode = "supabase" if DBT_TARGET == "supabase" else "local"
        logging.info("Running data pipeline with target_mode=%s dbt_target=%s", target_mode, DBT_TARGET)
        return target_mode

    @task
    def crawl_mangadex_raw() -> str:
        stdout = run_project_command(
            [
                sys.executable,
                "services/crawler-service/mangadex_raw_crawler.py",
                "--output-root",
                "data/raw",
                "--limit",
                str(param_value("limit", 10)),
                "--pages",
                str(param_value("pages", 1)),
                "--start-offset",
                str(param_value("start_offset", 0)),
                "--pause-seconds",
                str(param_value("pause_seconds", 0.5)),
                "--translated-language",
                str(param_value("translated_language", "en")),
            ]
        )

        match = re.search(r"^crawl_run_id=(?P<crawl_run_id>[^\s]+)$", stdout, flags=re.MULTILINE)
        if not match:
            raise RuntimeError("Crawler completed but did not print crawl_run_id=<id>.")

        crawl_run_id = match.group("crawl_run_id")
        logging.info("Captured crawl_run_id=%s", crawl_run_id)
        return crawl_run_id

    @task
    def raw_to_bronze(crawl_run_id: str) -> str:
        run_project_command(
            [
                sys.executable,
                "services/data-pipeline/mangadex_raw_to_bronze.py",
                "--raw-run-dir",
                run_dir("raw", crawl_run_id),
                "--output-root",
                "data/bronze",
                "--overwrite",
            ]
        )
        return crawl_run_id

    @task
    def bronze_to_silver(crawl_run_id: str) -> str:
        run_project_command(
            [
                sys.executable,
                "services/data-pipeline/mangadex_bronze_to_silver.py",
                "--bronze-run-dir",
                run_dir("bronze", crawl_run_id),
                "--output-root",
                "data/silver",
                "--overwrite",
            ]
        )
        return crawl_run_id

    @task
    def load_silver_to_postgres(crawl_run_id: str) -> str:
        run_project_command(
            [
                sys.executable,
                "services/data-pipeline/load_silver_to_postgres.py",
                "--silver-run-dir",
                run_dir("silver", crawl_run_id),
                "--database-url",
                DATABASE_URL,
                "--schema",
                "silver",
                "--overwrite",
            ],
            env=data_target_env(),
        )
        return crawl_run_id

    @task
    def dbt_build(crawl_run_id: str) -> str:
        run_project_command(
            [
                executable("dbt"),
                "build",
                "--project-dir",
                "services/dbt",
                "--profiles-dir",
                "services/dbt",
            ],
            env=data_target_env(),
        )
        return crawl_run_id

    @task
    def validate_gold_tables(crawl_run_id: str) -> dict[str, int]:
        counts: dict[str, int] = {}
        with psycopg.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                for table_name in GOLD_TABLES:
                    cur.execute(f'SELECT COUNT(*) FROM gold."{table_name}"')
                    counts[table_name] = int(cur.fetchone()[0])

        empty_tables = [table_name for table_name, count in counts.items() if count <= 0]
        if empty_tables:
            raise RuntimeError(f"Gold validation failed for crawl_run_id={crawl_run_id}; empty tables: {empty_tables}")

        logging.info("Gold validation counts for %s: %s", crawl_run_id, counts)
        return counts

    target = log_data_target()
    crawl = crawl_mangadex_raw()
    target >> crawl

    validate_gold_tables(
        dbt_build(
            load_silver_to_postgres(
                bronze_to_silver(
                    raw_to_bronze(crawl)
                )
            )
        )
    )


mangadex_data_pipeline()
