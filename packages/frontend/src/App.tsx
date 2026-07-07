import { BrowserRouter, Route, Routes } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AuthProvider } from "./hooks/useAuth";
import { ToastProvider } from "./components/ui/ToastProvider";
import { AuthGuard } from "./layouts/AuthGuard";
import { AppLayout } from "./layouts/AppLayout";
import { LoginPage } from "./routes/LoginPage";
import { ParentUpload } from "./routes/ParentUpload";
import { GameFrame } from "./routes/GameFrame";
import { ParentReport } from "./routes/ParentReport";
import { DoctorDashboard } from "./routes/DoctorDashboard";
import { NotFound } from "./routes/NotFound";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

export function App() {
  const childId = "child_demo_1"; // Default patient child ID for demo pathing

  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <ToastProvider>
          <BrowserRouter>
            <Routes>
              {/* Public route */}
              <Route path="/login" element={<LoginPage />} />

              {/* Protected Workspace Layout */}
              <Route element={<AuthGuard><AppLayout /></AuthGuard>}>
                <Route path="/" element={<ParentUpload childId={childId} />} />
                <Route path="/play/:childId" element={<GameFrame />} />
                <Route path="/report/:reportId" element={<ParentReport />} />
                <Route path="/doctor/:childId" element={<DoctorDashboard />} />
              </Route>

              {/* Friendly 404 Fallback */}
              <Route path="*" element={<NotFound />} />
            </Routes>
          </BrowserRouter>
        </ToastProvider>
      </AuthProvider>
    </QueryClientProvider>
  );
}
