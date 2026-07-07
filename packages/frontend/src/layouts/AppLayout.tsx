import { Link, Outlet, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { LogOut, User, Activity, BookOpen } from "lucide-react";

export function AppLayout() {
  const { user, role, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();

  async function handleLogout() {
    await logout();
    navigate("/login");
  }

  return (
    <div className="app-container">
      <nav className="navbar">
        <div className="nav-brand">
          <Activity size={24} color="var(--color-primary)" />
          ADHD<span>Quest</span>
        </div>
        
        <div className="nav-actions">
          {user && (
            <>
              {role === "parent" ? (
                <>
                  <Link
                    to="/"
                    className={`nav-link ${location.pathname === "/" ? "active" : ""}`}
                    style={{ display: "flex", alignItems: "center", gap: "0.25rem" }}
                  >
                    <BookOpen size={18} />
                    Upload Homework
                  </Link>
                </>
              ) : (
                <span className="role-badge doctor">Clinical View</span>
              )}

              <span className={`role-badge ${role}`}>
                {role}
              </span>

              <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", color: "var(--color-text-secondary)" }}>
                <User size={16} />
                <span style={{ fontSize: "0.9rem", fontWeight: "600" }}>{user.email}</span>
              </div>

              <button
                onClick={handleLogout}
                className="btn btn-outline"
                style={{ padding: "0.4rem 0.8rem", fontSize: "0.85rem", display: "flex", alignItems: "center", gap: "0.25rem" }}
              >
                <LogOut size={14} />
                Sign Out
              </button>
            </>
          )}
        </div>
      </nav>
      <main className="main-content">
        <Outlet />
      </main>
    </div>
  );
}
