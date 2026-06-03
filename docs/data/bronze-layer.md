# Bronze Layer

Bronze layer parses raw MangaDex responses into structured records for downstream processing. It stays close to the source shape and does not perform deep business normalization.

## Input

```text
data/raw/mangadex/crawl_run_id=<crawl_run_id>/
  manga/page_000001.json
  chapter/page_000001.json
  cover/page_000001.json
  author/page_000001.json
  tag/page_000001.json
  scanlation_group/page_000001.json
```

Each raw file contains:

```text
crawl_metadata
payload.data[]
payload.limit
payload.offset
payload.total
```

## Output

```text
data/bronze/mangadex/crawl_run_id=<crawl_run_id>/
  manga/entities.jsonl
  chapter/entities.jsonl
  cover/entities.jsonl
  author/entities.jsonl
  tag/entities.jsonl
  scanlation_group/entities.jsonl
  relationships/relationships.jsonl
  ingest_summary.json
  errors/errors.jsonl
```

JSONL is used so each line is one record. This format is easy to inspect locally and easy to load with Spark.

## Bronze Entity

Each entity record represents one item from `payload.data[]`.

```json
{
  "bronze_record_id": "mangadex:manga:<source_entity_id>:<crawl_run_id>",
  "source": "mangadex",
  "source_entity_type": "manga",
  "source_entity_id": "<source_entity_id>",
  "crawl_run_id": "<crawl_run_id>",
  "raw_file_path": "data/raw/mangadex/crawl_run_id=<crawl_run_id>/manga/page_000001.json",
  "raw_response_hash": "<sha256>",
  "raw_fetched_at": "2026-06-02T05:52:19Z",
  "bronze_ingested_at": "2026-06-02T06:00:00Z",
  "attributes": {},
  "relationships": []
}
```

## Bronze Relationship

Each relationship record represents one item from a MangaDex entity `relationships[]` array.

```json
{
  "bronze_relationship_id": "mangadex:manga:<from_id>:author:<to_id>:<crawl_run_id>",
  "source": "mangadex",
  "crawl_run_id": "<crawl_run_id>",
  "from_entity_type": "manga",
  "from_entity_id": "<manga_id>",
  "relationship_type": "author",
  "to_entity_type": "author",
  "to_entity_id": "<author_id>",
  "raw_file_path": "data/raw/mangadex/crawl_run_id=<crawl_run_id>/manga/page_000001.json",
  "bronze_ingested_at": "2026-06-02T06:00:00Z"
}
```

## ERD

```mermaid
erDiagram
    RAW_CRAWL_RUN ||--o{ RAW_API_RESPONSE : produces
    RAW_API_RESPONSE ||--o{ BRONZE_ENTITY : parsed_from
    RAW_API_RESPONSE ||--o{ BRONZE_RELATIONSHIP : parsed_from
    BRONZE_ENTITY ||--o{ BRONZE_RELATIONSHIP : has

    RAW_CRAWL_RUN {
        string crawl_run_id PK
        string source
        string status
        datetime started_at
        datetime ended_at
        string schema_version
    }

    RAW_API_RESPONSE {
        string raw_response_id PK
        string crawl_run_id FK
        string source
        string entity_type
        string endpoint
        string request_url
        json request_params
        int http_status
        datetime fetched_at
        string response_hash
        string raw_file_path
        string schema_version
    }

    BRONZE_ENTITY {
        string bronze_record_id PK
        string source
        string source_entity_type
        string source_entity_id
        string crawl_run_id FK
        string raw_file_path
        string raw_response_hash
        datetime raw_fetched_at
        datetime bronze_ingested_at
        json attributes
        json relationships
    }

    BRONZE_RELATIONSHIP {
        string bronze_relationship_id PK
        string source
        string crawl_run_id FK
        string from_entity_type
        string from_entity_id
        string relationship_type
        string to_entity_type
        string to_entity_id
        string raw_file_path
        datetime bronze_ingested_at
    }
```

## Validation Scope

Bronze performs lightweight validation only:

- `payload.result` is `ok`.
- `payload.data` is a list.
- Entity has `id`.
- Entity has `type`.
- `relationships` is a list when present.

Bronze does not:

- Deduplicate manga or chapters.
- Join author, tag, or cover data into manga.
- Normalize language fields.
- Build API-ready web tables.
- Translate content.

Those steps belong to Silver and Gold layers.
