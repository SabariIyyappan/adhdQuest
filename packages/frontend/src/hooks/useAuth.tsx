import { createContext, useContext, useState, useEffect } from "react";
import { bb } from "../lib/butterbase";

export type UserRole = "parent" | "doctor";

interface AuthUser {
  id: string;
  email: string;
  role: UserRole;
}

interface AuthContextType {
  user: AuthUser | null;
  role: UserRole | null;
  isAuthenticated: boolean;
  loading: boolean;
  loginAsMock: (role: UserRole) => void;
  signInWithGoogle: () => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState(true);

  // Sync auth state with Butterbase SDK session
  useEffect(() => {
    async function initAuth() {
      try {
        const session = bb.sessionManager.getSession();
        if (session?.user) {
          // Determine role from metadata or fallback to parent
          const role = (session.user.metadata?.role as UserRole) || "parent";
          setUser({
            id: session.user.id,
            email: session.user.email || "user@example.com",
            role,
          });
        } else {
          // Check local storage for mock dev login
          const storedMock = localStorage.getItem("adhdquest_mock_auth");
          if (storedMock) {
            setUser(JSON.parse(storedMock));
          }
        }
      } catch (err) {
        console.error("Auth initialization failed:", err);
      } finally {
        setLoading(false);
      }
    }
    initAuth();
  }, []);

  const loginAsMock = (role: UserRole) => {
    const mockUser: AuthUser = {
      id: role === "parent" ? "parent_demo_user" : "doctor_demo_user",
      email: role === "parent" ? "parent@example.com" : "doctor@clinical.org",
      role,
    };
    setUser(mockUser);
    localStorage.setItem("adhdquest_mock_auth", JSON.stringify(mockUser));
  };

  const signInWithGoogle = async () => {
    setLoading(true);
    try {
      const { url } = bb.auth.signInWithOAuth({
        provider: "google",
        redirectTo: window.location.origin,
      });
      if (url) {
        window.location.href = url;
      }
    } catch (err) {
      console.error("Sign in failed:", err);
      setLoading(false);
    }
  };

  const logout = async () => {
    setLoading(true);
    try {
      await bb.auth.signOut();
    } catch (err) {
      console.warn("Sign out from Butterbase error:", err);
    }
    setUser(null);
    localStorage.removeItem("adhdquest_mock_auth");
    setLoading(false);
  };

  const value: AuthContextType = {
    user,
    role: user?.role ?? null,
    isAuthenticated: !!user,
    loading,
    loginAsMock,
    signInWithGoogle,
    logout,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
