import type { ReactNode } from "react";
import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "./AuthContext";
import { LoadingBlock } from "../ui/StateBlock";

export function RequireAdmin({ children }: { children: ReactNode }) {
  const { loading, token, user } = useAuth();
  const location = useLocation();

  if (loading) {
    return <LoadingBlock />;
  }

  if (!token || !user) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  if (user.role !== "admin") {
    return <div className="state-block state-error">Admin access required.</div>;
  }

  return children;
}
