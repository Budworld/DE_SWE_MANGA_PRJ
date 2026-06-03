export interface PaginatedResponse<T> {
  items: T[];
  limit: number;
  offset: number;
  count: number;
}

export interface MangaCatalogItem {
  manga_id: string;
  source_manga_id: string;
  primary_title: string;
  primary_title_language: string | null;
  original_language: string | null;
  status: string | null;
  year: number | null;
  content_rating: string | null;
  publication_demographic: string | null;
  tag_names: string[];
  author_names: string[];
  cover_file_name: string | null;
  cover_url: string | null;
  latest_uploaded_chapter: string | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface MangaDetail extends MangaCatalogItem {
  alt_titles: Record<string, string>[];
  description: Record<string, string>;
  available_translated_languages: string[];
  artist_names: string[];
}

export interface ChapterListItem {
  chapter_id: string;
  source_chapter_id: string;
  source_manga_id: string | null;
  manga_id: string | null;
  manga_title: string | null;
  title: string | null;
  volume: string | null;
  chapter_number: string | null;
  translated_language: string | null;
  pages: number | null;
  scanlation_group_names: string[];
  publish_at: string | null;
  readable_at: string | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface LatestChapterItem {
  chapter_id: string;
  source_chapter_id: string;
  source_manga_id: string | null;
  manga_id: string | null;
  manga_title: string | null;
  cover_file_name: string | null;
  cover_url: string | null;
  title: string | null;
  chapter_number: string | null;
  translated_language: string | null;
  pages: number | null;
  publish_at: string | null;
  readable_at: string | null;
}

export interface ChapterPageItem {
  page_index: number;
  file_name: string;
  image_url: string;
}

export interface ChapterPagesResponse {
  source_chapter_id: string;
  quality: "data_saver" | "full";
  base_url: string;
  hash: string;
  pages: ChapterPageItem[];
}
