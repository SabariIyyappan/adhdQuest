/** Post-session parent report — summary, completion, attention arc, videos (Contract E). */

import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import type { SessionReport } from "@adhdquest/contracts";
import { bb } from "../lib/butterbase";
import { AttentionArcChart } from "../components/charts/AttentionArcChart";

export function ParentReport() {
  const { reportId = "" } = useParams();
  const [report, setReport] = useState<SessionReport | null>(null);

  useEffect(() => {
    bb.rest
      .select("reports", { id: reportId })
      .then((rows: { report_json: SessionReport }[]) => setReport(rows[0]?.report_json ?? null));
  }, [reportId]);

  if (!report) return <p>Loading report…</p>;

  const { session_summary, attention_arc, parent_summary } = report;
  return (
    <section className="parent-report">
      <h1>Session summary</h1>
      <p>{parent_summary}</p>
      <p>
        Completed {session_summary.levels_completed}/{session_summary.levels_total} levels (
        {Math.round(session_summary.completion_rate * 100)}%)
      </p>
      <AttentionArcChart data={attention_arc} />
      {/* "Share with doctor" action updates children.doctor_user_id */}
    </section>
  );
}
