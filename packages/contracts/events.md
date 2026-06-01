# Event Contracts

## chapter.crawled

```json
{
  "eventId": "uuid",
  "eventType": "chapter.crawled",
  "occurredAt": "2026-06-01T00:00:00Z",
  "sourceId": "source-name",
  "mangaExternalId": "external-id",
  "chapterExternalId": "external-id",
  "rawArtifactUri": "s3://bucket/raw/source/chapter.json"
}
```

## chapter.cleaned

```json
{
  "eventId": "uuid",
  "eventType": "chapter.cleaned",
  "occurredAt": "2026-06-01T00:00:00Z",
  "mangaId": "uuid",
  "chapterId": "uuid",
  "silverArtifactUri": "s3://bucket/silver/chapter.json"
}
```
