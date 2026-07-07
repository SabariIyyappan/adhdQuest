/** App routes — parent flow (upload -> play -> report) + doctor dashboard. */

import { BrowserRouter, Route, Routes } from "react-router-dom";
import { ParentUpload } from "./routes/ParentUpload";
import { GameFrame } from "./routes/GameFrame";
import { ParentReport } from "./routes/ParentReport";
import { DoctorDashboard } from "./routes/DoctorDashboard";

export function App() {
  // childId would come from the authed user's selected child profile.
  const childId = "TODO-selected-child";

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<ParentUpload childId={childId} />} />
        <Route path="/play/:childId" element={<GameFrame />} />
        <Route path="/report/:reportId" element={<ParentReport />} />
        <Route path="/doctor/:childId" element={<DoctorDashboard />} />
      </Routes>
    </BrowserRouter>
  );
}
