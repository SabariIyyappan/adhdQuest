# frontend — Person C (React SPA)

Parent upload flow, game frame, post-session report, and doctor dashboard. No backend
server: every call goes through the Butterbase TypeScript SDK (auth, REST, realtime).

## Layout

```
src/
  lib/butterbase.ts        SDK client (auth, REST, realtime subscribe).
  hooks/                   useSession (realtime), useReport, useAuth.
  routes/
    ParentUpload.tsx         select child + upload PDF -> "generating…"
    GameFrame.tsx            iframe game + live sidebar + replan overlay.
    ParentReport.tsx         post-session summary + attention arc + videos.
    DoctorDashboard.tsx      5 panels (plan §6 Feature 4).
  components/
    charts/                  AttentionArcChart, ReplanTrendChart, MedicationScatter.
    ReplanOverlay.tsx        "Adjusting your game…" + video card.
    CogneeQaPanel.tsx        doctor Q&A -> cognee-qa function.
  App.tsx, main.tsx
```

All cross-boundary shapes come from `@adhdquest/contracts` — never redefine them here.

## Run

```
npm install
npm run dev        # Vite dev server
npm run build      # -> dist/, deploy to Butterbase hosting
```
