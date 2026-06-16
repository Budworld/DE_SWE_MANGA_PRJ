import { Activity, Database, ExternalLink, ShieldCheck, TriangleAlert } from "lucide-react";
import { Link } from "react-router-dom";
import {
  getCatalogStats,
  getDataQualityChecks,
  getPipelineSummary,
  listPipelineRuns,
} from "../api/mangaApi";
import { useAsync } from "../hooks/useAsync";
import { ErrorBlock, LoadingBlock } from "../ui/StateBlock";

function numberValue(value: number | null | undefined): string {
  return new Intl.NumberFormat().format(value ?? 0);
}

function formatDate(value: string | null): string {
  return value ? new Date(value).toLocaleString() : "n/a";
}

export function AdminPage() {
  const summary = useAsync(() => getPipelineSummary(), []);
  const runs = useAsync(() => listPipelineRuns(12), []);
  const checks = useAsync(() => getDataQualityChecks(), []);
  const stats = useAsync(() => getCatalogStats(), []);
  const loading = summary.loading || runs.loading || checks.loading || stats.loading;
  const error = summary.error || runs.error || checks.error || stats.error;

  return (
    <section className="page">
      <div className="page-header">
        <div>
          <p className="eyebrow">Pipeline observability</p>
          <h1>Admin Dashboard</h1>
        </div>
        <div className="admin-links">
          <a href="http://localhost:8080" target="_blank" rel="noreferrer">
            Airflow <ExternalLink size={15} />
          </a>
          <a href="http://localhost:5050" target="_blank" rel="noreferrer">
            pgAdmin <ExternalLink size={15} />
          </a>
        </div>
      </div>

      {loading ? <LoadingBlock /> : null}
      {error ? <ErrorBlock message={error} /> : null}

      <div className="metric-grid">
        <article className="metric-card">
          <Database size={22} />
          <span>Gold Manga</span>
          <strong>{numberValue(summary.data?.gold_manga_count)}</strong>
        </article>
        <article className="metric-card">
          <Database size={22} />
          <span>Gold Chapters</span>
          <strong>{numberValue(summary.data?.gold_chapter_count)}</strong>
        </article>
        <article className="metric-card">
          <Activity size={22} />
          <span>Latest DAG</span>
          <strong>{summary.data?.latest_airflow_dag_state ?? "unknown"}</strong>
        </article>
        <article className="metric-card">
          <TriangleAlert size={22} />
          <span>Missing Covers</span>
          <strong>{numberValue(stats.data?.missing_cover_count)}</strong>
        </article>
      </div>

      <div className="admin-grid">
        <section className="admin-panel">
          <div className="section-title">
            <ShieldCheck size={20} />
            <h2>Data Quality</h2>
          </div>
          <div className="quality-list">
            {(checks.data ?? []).map((check) => (
              <div className="quality-row" key={check.check_name}>
                <span className={`status-pill status-${check.status}`}>{check.status}</span>
                <div>
                  <strong>{check.check_name}</strong>
                  <p>{check.description}</p>
                </div>
                <b>{numberValue(check.metric_value)}</b>
              </div>
            ))}
          </div>
        </section>

        <section className="admin-panel">
          <div className="section-title">
            <Database size={20} />
            <h2>Catalog Stats</h2>
          </div>
          <div className="stats-list">
            <p>Silver manga rows: {numberValue(summary.data?.silver_manga_rows)}</p>
            <p>Silver distinct manga: {numberValue(summary.data?.silver_distinct_manga)}</p>
            <p>Silver chapter rows: {numberValue(summary.data?.silver_chapter_rows)}</p>
            <p>Latest crawl run: {summary.data?.latest_crawl_run_id ?? "n/a"}</p>
            <p>Latest loaded at: {formatDate(summary.data?.latest_loaded_at ?? null)}</p>
          </div>
          <Link className="text-link" to="/catalog">
            Open catalog
          </Link>
        </section>
      </div>

      <section className="admin-panel">
        <div className="section-title">
          <Activity size={20} />
          <h2>Recent Pipeline Runs</h2>
        </div>
        <div className="table-wrap">
          <table className="admin-table">
            <thead>
              <tr>
                <th>Crawl run</th>
                <th>Loaded at</th>
                <th>Manga</th>
                <th>Chapters</th>
                <th>Covers</th>
                <th>Tags</th>
              </tr>
            </thead>
            <tbody>
              {(runs.data ?? []).map((run) => (
                <tr key={run.crawl_run_id}>
                  <td>{run.crawl_run_id}</td>
                  <td>{formatDate(run.loaded_at)}</td>
                  <td>{numberValue(run.manga_rows)}</td>
                  <td>{numberValue(run.chapter_rows)}</td>
                  <td>{numberValue(run.cover_rows)}</td>
                  <td>{numberValue(run.tag_rows)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="admin-panel">
        <div className="section-title">
          <Database size={20} />
          <h2>Gold Tables</h2>
        </div>
        <div className="gold-count-grid">
          {(summary.data?.gold_table_counts ?? []).map((table) => (
            <div className="gold-count" key={table.table_name}>
              <span>{table.table_name}</span>
              <strong>{numberValue(table.row_count)}</strong>
            </div>
          ))}
        </div>
      </section>
    </section>
  );
}
