import { LogIn } from "lucide-react";
import { FormEvent, useState } from "react";
import { Navigate, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

interface LoginLocationState {
  from?: { pathname?: string };
}

export function LoginPage() {
  const { login, token, user } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const state = location.state as LoginLocationState | null;
  const redirectTo = state?.from?.pathname ?? "/admin";
  const [username, setUsername] = useState("admin");
  const [password, setPassword] = useState("admin");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  if (token && user?.role === "admin") {
    return <Navigate to={redirectTo} replace />;
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      const loggedInUser = await login(username, password);
      if (loggedInUser.role === "admin") {
        navigate(redirectTo, { replace: true });
      } else {
        setError("This account does not have admin access.");
      }
    } catch {
      setError("Invalid username or password.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <section className="page login-page">
      <form className="login-panel" onSubmit={handleSubmit}>
        <div className="section-title">
          <LogIn size={22} />
          <h1>Admin Login</h1>
        </div>
        <label>
          Username
          <input value={username} onChange={(event) => setUsername(event.target.value)} />
        </label>
        <label>
          Password
          <input
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
          />
        </label>
        {error ? <p className="form-error">{error}</p> : null}
        <button className="primary-button" type="submit" disabled={submitting}>
          {submitting ? "Signing in..." : "Sign in"}
        </button>
      </form>
    </section>
  );
}
