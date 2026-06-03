# Crawler Service

Quản lý source adapters, crawl jobs, rate limit, retry và lưu raw artifacts.

## MangaDex raw crawler

Crawler đầu tiên dùng MangaDex API và lưu response nguyên bản vào `data/raw/mangadex`.

```powershell
python services/crawler-service/mangadex_raw_crawler.py --limit 10 --pages 1
```

Raw file có dạng:

```text
data/raw/mangadex/crawl_run_id=<run_id>/<entity_type>/page_000001.json
```

Nếu request lỗi mạng hoặc MangaDex chưa truy cập được, crawler vẫn ghi error artifact:

```text
data/raw/mangadex/crawl_run_id=<run_id>/errors/<entity_type>/page_000001.json
```

Chạy bằng Python bundled của Codex trên máy hiện tại:

```powershell
& "C:\Users\ASUS\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" services/crawler-service/mangadex_raw_crawler.py --limit 10 --pages 1 --pause-seconds 0.5
```
