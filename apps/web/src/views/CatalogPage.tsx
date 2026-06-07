import { Search } from "lucide-react";
import { FormEvent, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { listManga } from "../api/mangaApi";
import type { MangaCatalogItem } from "../api/types";
import { CoverImage } from "../ui/CoverImage";
import { ErrorBlock, LoadingBlock } from "../ui/StateBlock";

const PAGE_SIZE = 48;

export function CatalogPage() {
  const [draft, setDraft] = useState("");
  const [q, setQ] = useState("");
  const [status, setStatus] = useState("");
  const [language, setLanguage] = useState("");
  const [items, setItems] = useState<MangaCatalogItem[]>([]);
  const [count, setCount] = useState(0);
  const [offset, setOffset] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError(null);

    listManga({ q, status, original_language: language, limit: PAGE_SIZE, offset })
      .then((response) => {
        if (!active) {
          return;
        }

        setCount(response.count);
        setItems((current) => (offset === 0 ? response.items : [...current, ...response.items]));
      })
      .catch((caught: unknown) => {
        if (active) {
          setError(caught instanceof Error ? caught.message : "Unexpected error");
        }
      })
      .finally(() => {
        if (active) {
          setLoading(false);
        }
      });

    return () => {
      active = false;
    };
  }, [q, status, language, offset]);

  function submit(event: FormEvent) {
    event.preventDefault();
    setOffset(0);
    setQ(draft.trim());
  }

  function changeStatus(value: string) {
    setOffset(0);
    setStatus(value);
  }

  function changeLanguage(value: string) {
    setOffset(0);
    setLanguage(value);
  }

  const hasMore = items.length < count;

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
          <select value={status} onChange={(event) => changeStatus(event.target.value)}>
            <option value="">All status</option>
            <option value="ongoing">Ongoing</option>
            <option value="completed">Completed</option>
            <option value="hiatus">Hiatus</option>
            <option value="cancelled">Cancelled</option>
          </select>
          <select value={language} onChange={(event) => changeLanguage(event.target.value)}>
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
      <div className="catalog-summary">
        Showing {items.length} of {count} manga
      </div>
      <div className="manga-grid">
        {items.map((manga) => (
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
      {hasMore ? (
        <div className="load-more-row">
          <button type="button" onClick={() => setOffset(items.length)} disabled={loading}>
            {loading ? "Loading..." : "Load more"}
          </button>
        </div>
      ) : null}
    </section>
  );
}
