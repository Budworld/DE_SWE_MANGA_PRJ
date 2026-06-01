# Web Manga Platform

Skeleton cho dự án manga có thể phát triển theo hướng monorepo trước, sau đó tách dần thành microservices khi nghiệp vụ ổn định.

## Mục tiêu

- Crawl dữ liệu manga từ các nguồn hợp lệ.
- Làm sạch và chuẩn hóa dữ liệu theo pipeline kiểu DE.
- Triển khai web đọc manga.
- Dùng AI để dịch nội dung sang nhiều ngôn ngữ.
- Thiết kế đủ rõ để thực hành SWE, DE và AI trong cùng một hệ thống.

## Kiến trúc thư mục

```text
apps/
  web/                  Web đọc manga cho người dùng
  admin/                Trang quản trị nội dung, crawler jobs, bản dịch
services/
  api-gateway/          Entry point cho frontend
  auth-service/         Xác thực và phân quyền
  manga-service/        Domain manga, chapters, pages, metadata
  crawler-service/      Crawl nguồn dữ liệu
  data-pipeline/        Validate, clean, normalize, enrich dữ liệu
  ai-translation-service/ Dịch nội dung, OCR, post-processing
packages/
  shared/               Shared utilities
  contracts/            API contracts, event schemas, DTOs
  ui/                   Shared UI components
data/
  raw/                  Dữ liệu crawl nguyên bản
  bronze/               Dữ liệu đã ingest, ít biến đổi
  silver/               Dữ liệu đã clean/normalize
  gold/                 Dữ liệu phục vụ sản phẩm/analytics
  samples/              Dữ liệu mẫu nhỏ dùng cho dev/test
infra/
  docker/               Dockerfiles, compose fragments
  k8s/                  Kubernetes manifests
  terraform/            Cloud infrastructure
  monitoring/           Logs, metrics, tracing configs
docs/
  architecture/         ADRs, diagrams, service boundaries
  data/                 Data model, quality rules, lineage
  ai/                   Translation, OCR, evaluation
  api/                  API docs
scripts/                Local automation scripts
tests/                  E2E, integration, load tests
```

## Hướng triển khai đề xuất

1. Bắt đầu bằng monorepo và Docker Compose để giảm chi phí vận hành.
2. Giữ boundary theo service ngay từ đầu: API, crawler, data pipeline, AI translation.
3. Khi một phần đủ lớn hoặc cần scale riêng, tách service đó ra deploy độc lập.
4. Chuẩn hóa dữ liệu qua các lớp `raw -> bronze -> silver -> gold`.

## Lưu ý pháp lý

Crawler chỉ nên dùng với nguồn dữ liệu cho phép crawl, API công khai, hoặc dữ liệu bạn có quyền sử dụng.
