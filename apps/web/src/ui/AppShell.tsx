import { BookOpen, Clock3, Library } from "lucide-react";
import { NavLink, Outlet } from "react-router-dom";

export function AppShell() {
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <BookOpen size={24} />
          <span>Web Manga</span>
        </div>
        <nav className="nav">
          <NavLink to="/catalog">
            <Library size={18} />
            Catalog
          </NavLink>
          <NavLink to="/latest">
            <Clock3 size={18} />
            Latest
          </NavLink>
        </nav>
      </aside>
      <main className="main">
        <Outlet />
      </main>
    </div>
  );
}
