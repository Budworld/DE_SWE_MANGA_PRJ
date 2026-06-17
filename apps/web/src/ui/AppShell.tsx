import { Activity, BookOpen, Clock3, Library, LogIn, LogOut } from "lucide-react";
import { NavLink, Outlet } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

export function AppShell() {
  const { user, logout } = useAuth();

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
          <NavLink to="/admin">
            <Activity size={18} />
            Admin
          </NavLink>
        </nav>
        <div className="auth-menu">
          {user ? (
            <>
              <span>{user.username}</span>
              <button type="button" onClick={logout}>
                <LogOut size={16} />
                Logout
              </button>
            </>
          ) : (
            <NavLink to="/login">
              <LogIn size={18} />
              Login
            </NavLink>
          )}
        </div>
      </aside>
      <main className="main">
        <Outlet />
      </main>
    </div>
  );
}
