# Architecture Overview

## Context

Hệ thống phục vụ web đọc manga, pipeline crawl và chuẩn hóa dữ liệu, cùng AI translation cho nội dung nhiều ngôn ngữ.

## Service boundaries

- `api-gateway`: gom API cho frontend, auth middleware, rate limit.
- `auth-service`: user, session, role, permission.
- `manga-service`: manga, chapter, page, author, genre, reading progress.
- `crawler-service`: source adapters, crawl scheduling, raw artifact storage.
- `data-pipeline`: validation, deduplication, normalization, quality checks.
- `ai-translation-service`: OCR nếu cần, translation, glossary, review workflow.

## Communication

Giai đoạn đầu có thể dùng REST nội bộ và queue đơn giản. Khi hệ thống lớn hơn, ưu tiên event-driven cho các luồng:

- `chapter.crawled`
- `chapter.cleaned`
- `chapter.translation_requested`
- `chapter.translated`
- `chapter.published`
