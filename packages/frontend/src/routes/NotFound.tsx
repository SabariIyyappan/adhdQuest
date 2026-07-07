import { useNavigate } from "react-router-dom";
import { MoveLeft, HelpCircle } from "lucide-react";

export function NotFound() {
  const navigate = useNavigate();

  return (
    <div style={{
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      minHeight: "80vh",
      padding: "2rem",
      textAlign: "center"
    }}>
      <div className="card animate-pop" style={{
        maxWidth: "450px",
        width: "100%",
        padding: "2.5rem",
        display: "flex",
        flexDirection: "column",
        gap: "1.5rem",
        alignItems: "center"
      }}>
        <div className="animate-float" style={{ fontSize: "4rem" }}>
          🚀🌌
        </div>
        
        <div>
          <h1 style={{ fontSize: "1.75rem", fontWeight: "900", marginBottom: "0.5rem", display: "flex", alignItems: "center", gap: "0.5rem", justifyContent: "center" }}>
            <HelpCircle color="var(--color-accent)" size={24} />
            Lost in Space?
          </h1>
          <p style={{ color: "var(--color-text-secondary)", fontSize: "0.95rem" }}>
            We couldn't find that page, but don't worry! You can easily return to safe orbit.
          </p>
        </div>

        <button
          onClick={() => navigate("/")}
          className="btn btn-primary"
          style={{ padding: "0.8rem 1.5rem", display: "inline-flex", alignItems: "center", gap: "0.5rem" }}
        >
          <MoveLeft size={16} />
          Go back home
        </button>
      </div>
    </div>
  );
}
export default NotFound;
