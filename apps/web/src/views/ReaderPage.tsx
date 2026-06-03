import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { getChapterPages } from "../api/mangaApi";
import { useAsync } from "../hooks/useAsync";
import { ErrorBlock, LoadingBlock } from "../ui/StateBlock";

export function ReaderPage() {
  const { sourceChapterId = "" } = useParams();
  const [quality, setQuality] = useState<"data_saver" | "full">("data_saver");
  const { data, error, loading } = useAsync(() => getChapterPages(sourceChapterId, quality), [sourceChapterId, quality]);

  return (
    <section className="reader-page">
      <div className="reader-toolbar">
        <Link to="/latest">Back to latest</Link>
        <div className="segmented">
          <button className={quality === "data_saver" ? "active" : ""} onClick={() => setQuality("data_saver")}>
            Data saver
          </button>
          <button className={quality === "full" ? "active" : ""} onClick={() => setQuality("full")}>
            Full
          </button>
        </div>
      </div>

      {loading ? <LoadingBlock /> : null}
      {error ? <ErrorBlock message={error} /> : null}
      {data ? (
        <div className="reader-stack">
          {data.pages.map((page) => (
            <img key={page.page_index} src={page.image_url} alt={`Page ${page.page_index}`} loading="lazy" />
          ))}
        </div>
      ) : null}
    </section>
  );
}
