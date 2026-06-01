# Data Model Draft

## Core entities

- `Manga`: title, alternative titles, description, status, authors, genres.
- `Chapter`: manga id, chapter number, title, source, language, publish status.
- `Page`: chapter id, page index, image URI, width, height, checksum.
- `Translation`: chapter id, source language, target language, status, translated text, reviewer.
- `Source`: crawl source metadata, terms, rate limit, adapter config.

## Data layers

- `raw`: HTML, images, metadata response giữ nguyên từ source.
- `bronze`: dữ liệu đã parse sơ bộ, có schema cơ bản.
- `silver`: dữ liệu đã clean, deduplicate, normalize.
- `gold`: dữ liệu sẵn sàng cho API, search, analytics.

## Quality checks

- Manga title không rỗng.
- Chapter thuộc một manga hợp lệ.
- Page index liên tục trong mỗi chapter.
- Image checksum dùng để phát hiện trùng.
- Language code dùng ISO 639 khi có thể.
