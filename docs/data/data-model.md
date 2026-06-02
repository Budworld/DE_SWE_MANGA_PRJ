# Data Model Draft

## Core Entities

- `Manga`: title, alternative titles, description, status, authors, genres.
- `Chapter`: manga id, chapter number, title, source, language, publish status.
- `Page`: chapter id, page index, image URI, width, height, checksum.
- `Translation`: chapter id, source language, target language, status, translated text, reviewer.
- `Source`: crawl source metadata, terms, rate limit, adapter config.

## Data Layers

- `raw`: source responses and crawl metadata stored as immutable artifacts.
- `bronze`: parsed source-shaped records with light validation and lineage.
- `silver`: cleaned, deduplicated, normalized domain records.
- `gold`: API-ready, search-ready, and analytics-ready datasets.

Raw layer detail and ERD: [raw-layer.md](raw-layer.md).
Bronze layer detail and ERD: [bronze-layer.md](bronze-layer.md).
Silver layer detail and ERD: [silver-layer.md](silver-layer.md).

## Quality Checks

- Manga title is not empty.
- Chapter belongs to a valid manga.
- Page index is continuous within a chapter.
- Image checksum can be used to detect duplicates.
- Language code should follow ISO 639 where possible.
