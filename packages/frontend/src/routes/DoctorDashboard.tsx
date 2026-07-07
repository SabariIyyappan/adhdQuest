import { useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { getMedicationLogs } from "../lib/butterbase";
import { MultiSessionAttentionChart } from "../components/charts/MultiSessionAttentionChart";
import { ConceptBottleneckChart } from "../components/charts/ConceptBottleneckChart";
import { ReplanFrequencyChart } from "../components/charts/ReplanFrequencyChart";
import { MedicationScatterChart } from "../components/charts/MedicationScatterChart";
import { CogneeQaPanel } from "../components/CogneeQaPanel";
import { Shield, Activity, Calendar } from "lucide-react";

// Mock clinical dataset matching GDS results & curriculum prerequisites
const mockCentralityData = [
  { concept: "fractions", centrality: 0.84 },
  { concept: "division", centrality: 0.52 },
  { concept: "decimals", centrality: 0.35 },
  { concept: "multiplication", centrality: 0.18 },
  { concept: "word_problem", centrality: 0.12 }
];

const mockReplanFreqData = [
  { sessionName: "Sess 1", replans: 0 },
  { sessionName: "Sess 2", replans: 1 },
  { sessionName: "Sess 3", replans: 0 },
  { sessionName: "Sess 4", replans: 2 },
  { sessionName: "Sess 5", replans: 1 }
];

const mockMultiSessionData = [
  {
    id: "sess_4",
    label: "Session 4",
    points: [
      { minute: 2, errors: 0 },
      { minute: 4, errors: 2 },
      { minute: 6, errors: 1 },
      { minute: 8, errors: 3 },
      { minute: 10, errors: 4 },
      { minute: 12, errors: 1 },
      { minute: 14, errors: 0 }
    ]
  },
  {
    id: "sess_5",
    label: "Session 5 (Recent)",
    points: [
      { minute: 2, errors: 0 },
      { minute: 4, errors: 1 },
      { minute: 6, errors: 0 },
      { minute: 8, errors: 1 },
      { minute: 10, errors: 3 },
      { minute: 12, errors: 0 },
      { minute: 14, errors: 0 },
      { minute: 16, errors: 1 },
      { minute: 18, errors: 0 }
    ]
  }
];

const mockScatterData = [
  { timeDeltaMinutes: 30, attentionWindow: 12 },
  { timeDeltaMinutes: 60, attentionWindow: 18 },
  { timeDeltaMinutes: 90, attentionWindow: 20 },
  { timeDeltaMinutes: 120, attentionWindow: 15 },
  { timeDeltaMinutes: 180, attentionWindow: 10 },
  { timeDeltaMinutes: 240, attentionWindow: 8 }
];

export function DoctorDashboard() {
  const { childId = "child_demo_1" } = useParams();

  // Fetch medication logs (TanStack query)
  const { data: medLogs } = useQuery({
    queryKey: ["medLogs", childId],
    queryFn: () => getMedicationLogs(childId),
    staleTime: 60 * 1000
  });

  // Check if we should render medication panel (if database holds logs, or fallback to mock for demo)
  const hasMedicationData = (medLogs && medLogs.length > 0) || mockScatterData.length > 0;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "2rem" }} className="animate-slide-in">
      
      {/* Clinician Header bar */}
      <div className="card" style={{
        borderLeft: "4px solid var(--color-accent)",
        backgroundColor: "rgba(253, 203, 110, 0.02)",
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        flexWrap: "wrap",
        gap: "1rem"
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
          <div style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            width: "50px",
            height: "50px",
            borderRadius: "14px",
            backgroundColor: "rgba(253,203,110,0.1)",
            color: "var(--color-accent)"
          }}>
            <Shield size={26} />
          </div>
          <div>
            <h1 style={{ fontSize: "1.75rem", fontWeight: "900" }}>Clinical Assessment Dashboard</h1>
            <p style={{ color: "var(--color-text-secondary)", fontSize: "0.9rem" }}>
              Active Patient Profile: <strong>Alex (Age 9)</strong>
            </p>
          </div>
        </div>
        <div style={{ display: "flex", gap: "1.5rem" }}>
          <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end" }}>
            <span style={{ fontSize: "0.75rem", color: "var(--color-text-muted)", fontWeight: "700" }}>LAST ACTIVE</span>
            <span style={{ fontSize: "0.9rem", fontWeight: "800", display: "flex", alignItems: "center", gap: "0.25rem" }}>
              <Calendar size={14} color="var(--color-primary)" />
              Today (14:04)
            </span>
          </div>
        </div>
      </div>

      {/* Grid panels */}
      <div className="grid-2">
        {/* Panel 1: Multi Session Attention Curves */}
        <Panel
          title="Attention Arc Trend"
          description="Error metrics tracked chronologically over last sessions. Downward shifts signify attention fatigue points."
        >
          <MultiSessionAttentionChart sessions={mockMultiSessionData} />
        </Panel>

        {/* Panel 2: Concept Bottleneck (GDS Centrality) */}
        <Panel
          title="Prerequisite Bottlenecks"
          description="Graph centrality analysis (GDS Betweenness Centrality) mapping concepts causing recursive replans."
        >
          <ConceptBottleneckChart data={mockCentralityData} />
        </Panel>
      </div>

      <div className="grid-2">
        {/* Panel 3: Replan Frequency */}
        <Panel
          title="Replan Frequency Trend"
          description="Presents the count of struggle triggers (3+ fails on a single level) registered across sessions."
        >
          <ReplanFrequencyChart data={mockReplanFreqData} />
        </Panel>

        {/* Panel 4: Medication Correlation (Conditional Render) */}
        {hasMedicationData && (
          <Panel
            title="Medication Correlation Profile"
            description="Scatter plot correlating hours since dosage (X-axis) against active focus window (Y-axis)."
          >
            <MedicationScatterChart data={mockScatterData} />
          </Panel>
        )}
      </div>

      {/* Panel 5: Cognee clinical chatbot panel */}
      <div className="card">
        <h2 style={{ fontSize: "1.25rem", fontWeight: "900", marginBottom: "0.25rem", display: "flex", alignItems: "center", gap: "0.5rem" }}>
          <Activity size={20} color="var(--color-accent)" />
          Recall Knowledge Query (Cognee memory)
        </h2>
        <p style={{ fontSize: "0.85rem", color: "var(--color-text-secondary)", marginBottom: "1.25rem" }}>
          Interact directly with the child's knowledge graph database to query specific concepts, progression pathways, or struggle occurrences.
        </p>
        <CogneeQaPanel childId={childId} />
      </div>

    </div>
  );
}

function Panel({
  title,
  description,
  children
}: {
  title: string;
  description: string;
  children: React.ReactNode;
}) {
  return (
    <div className="card" style={{ display: "flex", flexDirection: "column", height: "100%" }}>
      <h2 style={{ fontSize: "1.25rem", fontWeight: "900" }}>{title}</h2>
      <p style={{ fontSize: "0.8rem", color: "var(--color-text-secondary)", marginBottom: "1.25rem", lineHeight: 1.4 }}>
        {description}
      </p>
      <div className="chart-container" style={{ flex: 1, display: "flex", alignItems: "center" }}>
        {children}
      </div>
    </div>
  );
}
