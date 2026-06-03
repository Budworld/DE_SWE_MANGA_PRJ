import { Search } from "lucide-react";
import { FormEvent, useState } from "react";
import { Link } from "react-router-dom";
import { listManga } from "../api/mangaApi";
import { useAsync } from "../hooks/useAsync";
import { CoverImage } from "../ui/CoverImage";
import { ErrorBlock, LoadingBlock } from "../ui/StateBlock";

export function CatalogPage() {
  const [draft, setDraft] = useState("");
  const [q, setQ] = useState("");
  const [status, setStatus] = useState("");
  const [language, setLanguage] = useState("");
  const { data, error, loading } = useAsync(
    () => listManga({ q, status, original_language: language, limit: 24, offset: 0 }),
    [q, status, language],
  );

  function submit(event: FormEvent) {
    event.preventDefault();
    setQ(draft.trim());
  }

  return (
    <section className="page">
      <div className="page-header">
        <div>
          <p className="eyebrow">Gold catalog</p>
          <h1>Manga Catalog</h1>
        </div>
        <form className="toolbar" onSubmit={submit}>
          <label className="search-box">
            <Search size={18} />
            <input value={draft} onChange={(event) => setDraft(event.target.value)} placeholder="Search title" />
          </label>
          <select value={status} onChange={(event) => setStatus(event.target.value)}>
            <option value="">All status</option>
            <option value="ongoing">Ongoing</option>
            <option value="completed">Completed</option>
            <option value="hiatus">Hiatus</option>
            <option value="cancelled">Cancelled</option>
          </select>
          <select value={language} onChange={(event) => setLanguage(event.target.value)}>
            <option value="">All original languages</option>
            <option value="ja">Japanese</option>
            <option value="ko">Korean</option>
            <option value="zh">Chinese</option>
          </select>
          <button type="submit">Search</button>
        </form>
      </div>

      {loading ? <LoadingBlock /> : null}
      {error ? <ErrorBlock message={error} /> : null}
      {data ? (
        <div className="manga-grid">
          {data.items.map((manga) => (
            <Link className="manga-card" to={`/manga/${encodeURIComponent(manga.manga_id)}`} key={manga.manga_id}>
              <CoverImage src={manga.cover_url} title={manga.primary_title} />
              <div className="card-body">
                <h2>{manga.primary_title}</h2>
                <p>{[manga.status, manga.original_language, manga.year].filter(Boolean).join(" / ")}</p>
                <div className="chip-row">
                  {manga.tag_names.slice(0, 3).map((tag) => (
                    <span className="chip" key={tag}>
                      {tag}
                    </span>
                  ))}
                </div>
              </div>
            </Link>
          ))}
        </div>
      ) : null}
    </section>
  );
}
