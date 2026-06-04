import { BookOpen } from "lucide-react";
import { Link, useParams } from "react-router-dom";
import { getManga, listMangaChapters } from "../api/mangaApi";
import { useAsync } from "../hooks/useAsync";
import { CoverImage } from "../ui/CoverImage";
import { ErrorBlock, LoadingBlock } from "../ui/StateBlock";

export function MangaDetailPage() {
  const { mangaId = "" } = useParams();
  const manga = useAsync(() => getManga(mangaId), [mangaId]);
  const chapters = useAsync(() => listMangaChapters(mangaId, { limit: 100, offset: 0 }), [mangaId]);

  if (manga.loading) return <LoadingBlock />;
  if (manga.error) return <ErrorBlock message={manga.error} />;
  if (!manga.data) return null;

  const description = manga.data.description.en ?? Object.values(manga.data.description)[0] ?? "No description available.";

  return (
    <section className="page">
      <div className="detail-layout">
        <CoverImage src={manga.data.cover_url} title={manga.data.primary_title} large />
        <div className="detail-main">
          <p className="eyebrow">Manga detail</p>
          <h1>{manga.data.primary_title}</h1>
          <p className="description">{description}</p>
          <div className="meta-grid">
            <span>Status: {manga.data.status ?? "Unknown"}</span>
            <span>Original: {manga.data.original_language ?? "Unknown"}</span>
            <span>Year: {manga.data.year ?? "Unknown"}</span>
            <span>Rating: {manga.data.content_rating ?? "Unknown"}</span>
          </div>
          <div className="chip-row">
            {manga.data.tag_names.map((tag) => (
              <span className="chip" key={tag}>
                {tag}
              </span>
            ))}
          </div>
        </div>
      </div>

      <div className="section-title">
        <BookOpen size={20} />
        <h2>Chapters</h2>
      </div>
      {chapters.loading ? <LoadingBlock /> : null}
      {chapters.error ? <ErrorBlock message={chapters.error} /> : null}
      {chapters.data ? (
        <div className="chapter-list">
          {chapters.data.items.map((chapter) => (
            <Link className="chapter-row" key={chapter.chapter_id} to={`/chapters/${chapter.source_chapter_id}/read`}>
              <strong>Chapter {chapter.chapter_number ?? "?"}</strong>
              <span>{chapter.title || "Untitled"}</span>
              <small>{chapter.translated_language ?? "unknown"} / {chapter.pages ?? 0} pages</small>
            </Link>
          ))}
        </div>
      ) : null}
    </section>
  );
}
