import { Link } from "react-router-dom";
import { listLatestChapters } from "../api/mangaApi";
import { useAsync } from "../hooks/useAsync";
import { CoverImage } from "../ui/CoverImage";
import { ErrorBlock, LoadingBlock } from "../ui/StateBlock";

export function LatestPage() {
  const { data, error, loading } = useAsync(() => listLatestChapters({ limit: 30, offset: 0 }), []);

  return (
    <section className="page">
      <div className="page-header">
        <div>
          <p className="eyebrow">Latest updates</p>
          <h1>Latest Chapters</h1>
        </div>
      </div>
      {loading ? <LoadingBlock /> : null}
      {error ? <ErrorBlock message={error} /> : null}
      {data ? (
        <div className="latest-list">
          {data.items.map((chapter) => (
            <Link className="latest-row" key={chapter.chapter_id} to={`/chapters/${chapter.source_chapter_id}/read`}>
              <CoverImage src={chapter.cover_url} title={chapter.manga_title ?? "Manga"} />
              <div>
                <h2>{chapter.manga_title ?? "Untitled manga"}</h2>
                <p>Chapter {chapter.chapter_number ?? "?"} / {chapter.translated_language ?? "unknown"}</p>
              </div>
            </Link>
          ))}
        </div>
      ) : null}
    </section>
  );
}
