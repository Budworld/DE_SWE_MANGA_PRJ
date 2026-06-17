import type {
  ChapterListItem,
  ChapterPagesResponse,
  CatalogStatsResponse,
  DataQualityCheckItem,
  AuthUser,
  LatestChapterItem,
  LoginResponse,
  MangaCatalogItem,
  MangaDetail,
  PaginatedResponse,
  PipelineRunItem,
  PipelineSummaryResponse,
} from "./types";

const API_BASE_URL = import.meta.env.VITE_MANGA_API_URL ?? "http://localhost:8000";

function getStoredToken(): string | null {
  return localStorage.getItem("web_manga_auth_token");
}

function authHeaders(): HeadersInit {
  const token = getStoredToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function requestJson<T>(path: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      ...authHeaders(),
      ...init.headers,
    },
  });
  if (!response.ok) {
    throw new Error(`API request failed: ${response.status}`);
  }
  return response.json() as Promise<T>;
}

async function getJson<T>(path: string): Promise<T> {
  return requestJson<T>(path);
}

function query(params: Record<string, string | number | undefined | null>): string {
  const search = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") {
      search.set(key, String(value));
    }
  });
  const value = search.toString();
  return value ? `?${value}` : "";
}

export function listManga(params: {
  q?: string;
  status?: string;
  original_language?: string;
  limit?: number;
  offset?: number;
}) {
  return getJson<PaginatedResponse<MangaCatalogItem>>(`/manga${query(params)}`);
}

export function getManga(mangaId: string) {
  return getJson<MangaDetail>(`/manga/${encodeURIComponent(mangaId)}`);
}

export function listMangaChapters(
  mangaId: string,
  params: { translated_language?: string; limit?: number; offset?: number },
) {
  return getJson<PaginatedResponse<ChapterListItem>>(
    `/manga/${encodeURIComponent(mangaId)}/chapters${query(params)}`,
  );
}

export function listLatestChapters(params: {
  translated_language?: string;
  limit?: number;
  offset?: number;
}) {
  return getJson<PaginatedResponse<LatestChapterItem>>(`/chapters/latest${query(params)}`);
}

export function getChapterPages(
  sourceChapterId: string,
  quality: "data_saver" | "full",
) {
  return getJson<ChapterPagesResponse>(
    `/chapters/${encodeURIComponent(sourceChapterId)}/pages${query({ quality })}`,
  );
}

export function login(username: string, password: string) {
  return requestJson<LoginResponse>("/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
}

export function getCurrentUser() {
  return getJson<AuthUser>("/auth/me");
}

export function getPipelineSummary() {
  return getJson<PipelineSummaryResponse>("/admin/pipeline/summary");
}

export function listPipelineRuns(limit = 10) {
  return getJson<PipelineRunItem[]>(`/admin/pipeline/runs${query({ limit })}`);
}

export function getDataQualityChecks() {
  return getJson<DataQualityCheckItem[]>("/admin/data-quality");
}

export function getCatalogStats() {
  return getJson<CatalogStatsResponse>("/admin/catalog/stats");
}
