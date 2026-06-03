# Silver Layer

Silver layer transforms Bronze source-shaped records into cleaned, normalized domain records. This is the first layer where business meaning becomes explicit.

Silver still stays close to MangaDex as the only source, but it removes nested source noise, extracts key fields, and creates bridge tables for relationships.

## Input

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
```

## Output

```text
data/silver/mangadex/crawl_run_id=<crawl_run_id>/
  manga.jsonl
  chapter.jsonl
  cover.jsonl
  author.jsonl
  tag.jsonl
  scanlation_group.jsonl
  manga_author.jsonl
  manga_artist.jsonl
  manga_tag.jsonl
  manga_cover.jsonl
  chapter_manga.jsonl
  chapter_scanlation_group.jsonl
  transform_summary.json
  errors/errors.jsonl
```

## Silver Records

### silver_manga

```text
manga_id
source
source_manga_id
primary_title
primary_title_language
alt_titles
description
original_language
available_translated_languages
publication_demographic
status
year
content_rating
created_at
updated_at
latest_uploaded_chapter
crawl_run_id
bronze_record_id
silver_transformed_at
```

### silver_chapter

```text
chapter_id
source
source_chapter_id
source_manga_id
title
volume
chapter_number
translated_language
external_url
pages
version
publish_at
readable_at
created_at
updated_at
crawl_run_id
bronze_record_id
silver_transformed_at
```

### silver_cover

```text
cover_id
source
source_cover_id
source_manga_id
volume
file_name
description
locale
created_at
updated_at
crawl_run_id
bronze_record_id
silver_transformed_at
```

### silver_author

```text
author_id
source
source_author_id
name
biography
image_url
website
twitter
pixiv
created_at
updated_at
crawl_run_id
bronze_record_id
silver_transformed_at
```

### silver_tag

```text
tag_id
source
source_tag_id
name
description
group_name
version
crawl_run_id
bronze_record_id
silver_transformed_at
```

### silver_scanlation_group

```text
scanlation_group_id
source
source_group_id
name
alt_names
website
discord
contact_email
description
created_at
updated_at
crawl_run_id
bronze_record_id
silver_transformed_at
```

## Bridge Tables

Bridge tables are extracted from Bronze relationships.

```text
manga_author
manga_artist
manga_tag
manga_cover
chapter_manga
chapter_scanlation_group
```

Each bridge keeps:

```text
source
crawl_run_id
from_entity_id
to_entity_id
relationship_type
bronze_relationship_id
silver_transformed_at
```

## ERD

```mermaid
erDiagram
    SILVER_MANGA ||--o{ SILVER_CHAPTER_MANGA : has_chapter
    SILVER_CHAPTER ||--o{ SILVER_CHAPTER_MANGA : belongs_to_manga

    SILVER_MANGA ||--o{ SILVER_MANGA_AUTHOR : has_author
    SILVER_AUTHOR ||--o{ SILVER_MANGA_AUTHOR : authors_manga

    SILVER_MANGA ||--o{ SILVER_MANGA_ARTIST : has_artist
    SILVER_AUTHOR ||--o{ SILVER_MANGA_ARTIST : draws_manga

    SILVER_MANGA ||--o{ SILVER_MANGA_TAG : has_tag
    SILVER_TAG ||--o{ SILVER_MANGA_TAG : tags_manga

    SILVER_MANGA ||--o{ SILVER_MANGA_COVER : has_cover
    SILVER_COVER ||--o{ SILVER_MANGA_COVER : cover_for_manga

    SILVER_CHAPTER ||--o{ SILVER_CHAPTER_SCANLATION_GROUP : translated_by
    SILVER_SCANLATION_GROUP ||--o{ SILVER_CHAPTER_SCANLATION_GROUP : group_for_chapter

    SILVER_MANGA {
        string manga_id PK
        string source
        string source_manga_id
        string primary_title
        string primary_title_language
        json alt_titles
        json description
        string original_language
        json available_translated_languages
        string publication_demographic
        string status
        int year
        string content_rating
        datetime created_at
        datetime updated_at
        string latest_uploaded_chapter
    }

    SILVER_CHAPTER {
        string chapter_id PK
        string source
        string source_chapter_id
        string source_manga_id
        string title
        string volume
        string chapter_number
        string translated_language
        string external_url
        int pages
        int version
        datetime publish_at
        datetime readable_at
        datetime created_at
        datetime updated_at
    }

    SILVER_COVER {
        string cover_id PK
        string source
        string source_cover_id
        string source_manga_id
        string volume
        string file_name
        string locale
        datetime created_at
        datetime updated_at
    }

    SILVER_AUTHOR {
        string author_id PK
        string source
        string source_author_id
        string name
        json biography
        string image_url
        string website
        string twitter
        string pixiv
    }

    SILVER_TAG {
        string tag_id PK
        string source
        string source_tag_id
        json name
        json description
        string group_name
        int version
    }

    SILVER_SCANLATION_GROUP {
        string scanlation_group_id PK
        string source
        string source_group_id
        string name
        json alt_names
        string website
        string discord
        string contact_email
    }

    SILVER_MANGA_AUTHOR {
        string source_manga_id FK
        string source_author_id FK
    }

    SILVER_MANGA_ARTIST {
        string source_manga_id FK
        string source_author_id FK
    }

    SILVER_MANGA_TAG {
        string source_manga_id FK
        string source_tag_id FK
    }

    SILVER_MANGA_COVER {
        string source_manga_id FK
        string source_cover_id FK
    }

    SILVER_CHAPTER_MANGA {
        string source_chapter_id FK
        string source_manga_id FK
    }

    SILVER_CHAPTER_SCANLATION_GROUP {
        string source_chapter_id FK
        string source_group_id FK
    }
```

## Validation Scope

Silver performs domain-level checks:

- Manga must have `source_manga_id`.
- Manga should have a non-empty `primary_title`.
- Chapter must have `source_chapter_id`.
- Chapter should have `translated_language`.
- Cover should have `file_name`.
- Author should have `name`.
- Tag should have `name`.

Failed records are written to `errors/errors.jsonl`.

## Not In Silver

Silver does not build final web views, search indexes, or analytics marts. Those belong to Gold.
