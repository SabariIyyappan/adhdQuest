import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { LoadingSkeleton } from "../components/ui/LoadingSkeleton";

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <div style={{ display: "flex", flexDirection: "column", gap: "1rem", padding: "2rem", maxWidth: "600px", margin: "10% auto" }}>
        <LoadingSkeleton height={40} width="60%" />
        <LoadingSkeleton height={20} />
        <LoadingSkeleton height={20} />
        <LoadingSkeleton height={20} />
      </div>
    );
  }

  if (!isAuthenticated) {
    // Save the current location they were trying to access
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return <>{children}</>;
}
