import { useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { useToast } from "../components/ui/ToastProvider";
import { LogIn, Sparkles, ShieldCheck } from "lucide-react";

export function LoginPage() {
  const { loginAsMock, signInWithGoogle } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const { success } = useToast();

  // Redirect target after successful login
  const from = (location.state as any)?.from?.pathname || "/";

  function handleMockLogin(role: "parent" | "doctor") {
    loginAsMock(role);
    success(`Logged in successfully as a Demo ${role}!`);
    
    // Redirect doctors to a child profile dashboard view directly
    if (role === "doctor") {
      navigate("/doctor/child_demo_1");
    } else {
      navigate(from);
    }
  }

  return (
    <div style={{
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      minHeight: "100vh",
      padding: "2rem",
      backgroundColor: "var(--color-bg)"
    }}>
      <div className="card animate-pop" style={{
        maxWidth: "480px",
        width: "100%",
        padding: "2.5rem",
        display: "flex",
        flexDirection: "column",
        gap: "1.5rem",
        textAlign: "center",
        border: "1px solid var(--color-border)"
      }}>
        <div>
          <div className="animate-float" style={{
            display: "inline-flex",
            alignItems: "center",
            justifyContent: "center",
            width: "64px",
            height: "64px",
            borderRadius: "20px",
            backgroundColor: "rgba(108, 92, 231, 0.15)",
            color: "var(--color-primary)",
            fontSize: "2rem",
            marginBottom: "1rem"
          }}>
            🎓
          </div>
          <h1 style={{ fontSize: "2rem", fontWeight: "900", marginBottom: "0.5rem" }}>
            ADHD<span style={{ color: "var(--color-primary)" }}>Quest</span>
          </h1>
          <p style={{ color: "var(--color-text-secondary)", fontSize: "0.95rem" }}>
            Agentic homework learning companion for ADHD children (ages 8–13).
          </p>
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem", margin: "1rem 0" }}>
          <button
            onClick={signInWithGoogle}
            className="btn btn-primary"
            style={{ width: "100%", padding: "1rem" }}
          >
            <LogIn size={20} />
            Sign in with Google
          </button>
        </div>

        <div style={{ position: "relative", textAlign: "center", margin: "0.5rem 0" }}>
          <hr style={{ borderColor: "var(--color-border)" }} />
          <span style={{
            position: "absolute",
            top: "50%",
            left: "50%",
            transform: "translate(-50%, -50%)",
            backgroundColor: "var(--color-surface)",
            padding: "0 0.75rem",
            fontSize: "0.8rem",
            color: "var(--color-text-muted)",
            fontWeight: "700",
            textTransform: "uppercase"
          }}>
            Developer Sandbox
          </span>
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
          <p style={{ fontSize: "0.8rem", color: "var(--color-text-secondary)", fontWeight: "600" }}>
            Simulate roles locally without active database keys:
          </p>
          <div style={{ display: "flex", gap: "1rem" }}>
            <button
              onClick={() => handleMockLogin("parent")}
              className="btn btn-outline"
              style={{ flex: 1, borderColor: "var(--color-primary)", color: "var(--color-primary)", display: "flex", flexDirection: "column", gap: "0.25rem", padding: "0.75rem" }}
            >
              <Sparkles size={16} />
              <span style={{ fontSize: "0.85rem", fontWeight: "800" }}>Parent Portal</span>
            </button>
            <button
              onClick={() => handleMockLogin("doctor")}
              className="btn btn-outline"
              style={{ flex: 1, borderColor: "var(--color-accent)", color: "var(--color-accent)", display: "flex", flexDirection: "column", gap: "0.25rem", padding: "0.75rem" }}
            >
              <ShieldCheck size={16} />
              <span style={{ fontSize: "0.85rem", fontWeight: "800" }}>Doctor Portal</span>
            </button>
          </div>
        </div>

        <div style={{ fontSize: "0.75rem", color: "var(--color-text-muted)", fontWeight: "600" }}>
          COPPA-safe & Secure. Powered by Butterbase.
        </div>
      </div>
    </div>
  );
}
