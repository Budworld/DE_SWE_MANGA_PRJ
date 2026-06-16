import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { AppShell } from "./ui/AppShell";
import { AdminPage } from "./views/AdminPage";
import { CatalogPage } from "./views/CatalogPage";
import { LatestPage } from "./views/LatestPage";
import { MangaDetailPage } from "./views/MangaDetailPage";
import { ReaderPage } from "./views/ReaderPage";
import "./styles.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <BrowserRouter>
      <Routes>
        <Route element={<AppShell />}>
          <Route index element={<Navigate to="/catalog" replace />} />
          <Route path="/catalog" element={<CatalogPage />} />
          <Route path="/latest" element={<LatestPage />} />
          <Route path="/admin" element={<AdminPage />} />
          <Route path="/manga/:mangaId" element={<MangaDetailPage />} />
          <Route path="/chapters/:sourceChapterId/read" element={<ReaderPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  </React.StrictMode>,
);
