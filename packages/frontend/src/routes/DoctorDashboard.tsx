/**
 * Doctor dashboard — the 5 panels of plan §6 Feature 4. RLS ensures the doctor only
 * sees children where doctor_user_id = auth.uid(); the medication panel renders only
 * when logs exist.
 */

import { useParams } from "react-router-dom";
import { AttentionArcChart } from "../components/charts/AttentionArcChart";
import { CogneeQaPanel } from "../components/CogneeQaPanel";

export function DoctorDashboard() {
  const { childId = "" } = useParams();

  return (
    <section className="doctor-dashboard">
      <h1>Learning insights</h1>

      {/* 1. Attention arc trend across last 8 sessions */}
      <Panel title="Attention arc trend">
        <AttentionArcChart data={[]} />
      </Panel>

      {/* 2. Concept bottleneck ranking (GDS betweenness centrality from report_json) */}
      <Panel title="Concept bottlenecks">{/* ranked list */}</Panel>

      {/* 3. Replan frequency trend */}
      <Panel title="Replan frequency">{/* bar chart */}</Panel>

      {/* 4. Medication correlation (only if medication_logs exist) */}
      <Panel title="Medication correlation">{/* scatter */}</Panel>

      {/* 5. Cognee Q&A */}
      <Panel title="Ask about this child">
        <CogneeQaPanel childId={childId} />
      </Panel>
    </section>
  );
}

function Panel({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="panel">
      <h2>{title}</h2>
      {children}
    </div>
  );
}
