import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import type { SessionReport } from "@adhdquest/contracts";
import { bb, shareWithDoctor, logMedication } from "../lib/butterbase";
import { AttentionArcChart } from "../components/charts/AttentionArcChart";
import { StatCard } from "../components/ui/StatCard";
import { useToast } from "../components/ui/ToastProvider";
import { Award, Clock, AlertTriangle, ShieldCheck, Heart, Plus, Mail } from "lucide-react";

// High fidelity mock data matching Contract E for demo evaluation
const mockReport: SessionReport = {
  session_summary: {
    total_minutes: 18,
    levels_completed: 8,
    levels_total: 10,
    completion_rate: 0.8,
    replan_count: 1,
    videos_watched: 1
  },
  attention_arc: [
    { minute: 2, errors: 0 },
    { minute: 4, errors: 1 },
    { minute: 6, errors: 0 },
    { minute: 8, errors: 1 },
    { minute: 10, errors: 3 }, // struggle point (fraction level 3)
    { minute: 12, errors: 0 }, // post-replan recovery
    { minute: 14, errors: 0 },
    { minute: 16, errors: 1 },
    { minute: 18, errors: 0 }
  ],
  concept_performance: [
    { concept: "addition", avg_time_seconds: 45, fail_rate: 0, replan_triggered: false },
    { concept: "subtraction", avg_time_seconds: 55, fail_rate: 0, replan_triggered: false },
    { concept: "multiplication", avg_time_seconds: 90, fail_rate: 0.1, replan_triggered: false },
    { concept: "division", avg_time_seconds: 120, fail_rate: 0.2, replan_triggered: false },
    { concept: "fractions", avg_time_seconds: 240, fail_rate: 0.6, replan_triggered: true }
  ],
  bottleneck_concept: "fractions",
  bottleneck_centrality_score: 0.84,
  parent_summary: "Alex did an outstanding job today! He showed great focus in the early levels on addition and multiplication. He hit a brief speed bump on fractions (Level 5), but after taking a short video lesson break, he successfully worked through a simpler visual fractions maze. The session ended with high energy!",
  doctor_narrative: "Patient exhibited classic executive function fatigue at the 10-minute mark coinciding with fractions presentation. Centrality analysis identifies fractions concept as a significant bottleneck (betweenness centrality: 0.84). High recovery rate following structured video replan intervention, indicating positive reinforcement with tactile visual mechanics.",
  next_session_recommendations: {
    suggested_duration_minutes: 15,
    prioritize_concepts: ["fractions", "division"],
    start_with_concept: "multiplication"
  },
  medication_correlation: null
};

export function ParentReport() {
  const { reportId = "" } = useParams();
  const [report, setReport] = useState<SessionReport | null>(null);
  const [sharingEmail, setSharingEmail] = useState("");
  const [shareLoading, setShareLoading] = useState(false);
  
  // Medication log state
  const [medName, setMedName] = useState("");
  const [medDose, setMedDose] = useState("");
  const [medLoading, setMedLoading] = useState(false);

  const { success, error } = useToast();

  useEffect(() => {
    if (reportId.includes("mock") || reportId === "report_demo_1") {
      setReport(mockReport);
    } else {
      bb.from("reports")
        .select("*")
        .eq("id", reportId)
        .execute()
        .then(({ data }: any) => {
          if (data && data.length > 0) {
            setReport(data[0].report_json ?? mockReport);
          } else {
            setReport(mockReport);
          }
        })
        .catch(() => {
          setReport(mockReport);
        });
    }
  }, [reportId]);

  async function handleShare(e: React.FormEvent) {
    e.preventDefault();
    if (!sharingEmail) return;
    setShareLoading(true);
    try {
      // child_demo_1 used for mockup
      await shareWithDoctor("child_demo_1", sharingEmail);
      success(`Shared successfully with Dr. ${sharingEmail.split("@")[0]}!`);
      setSharingEmail("");
    } catch (err) {
      error("Sharing failed.");
    } finally {
      setShareLoading(false);
    }
  }

  async function handleLogMed(e: React.FormEvent) {
    e.preventDefault();
    if (!medName || !medDose) return;
    setMedLoading(true);
    try {
      await logMedication("child_demo_1", medName, parseFloat(medDose));
      success(`Logged medication: ${medName} ${medDose}mg`);
      setMedName("");
      setMedDose("");
    } catch (err) {
      error("Failed to log medication.");
    } finally {
      setMedLoading(false);
    }
  }

  if (!report) return <p style={{ padding: "2rem" }}>Loading report...</p>;

  const { session_summary, attention_arc, concept_performance, parent_summary, next_session_recommendations } = report;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "2rem" }} className="animate-slide-in">
      
      {/* 1. Header & Summary Hero */}
      <div className="card" style={{
        backgroundImage: "linear-gradient(135deg, rgba(108, 92, 231, 0.1) 0%, rgba(26, 26, 46, 0) 100%)",
        border: "1px solid rgba(108, 92, 231, 0.2)"
      }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "1rem" }}>
          <div>
            <span style={{ fontSize: "0.8rem", color: "var(--color-primary)", fontWeight: "900", textTransform: "uppercase", letterSpacing: "0.05em" }}>
              Quest Report
            </span>
            <h1 style={{ fontSize: "2.25rem", fontWeight: "900", marginTop: "0.25rem" }}>Alex's Learning Journey</h1>
          </div>
          <Link to="/doctor/child_demo_1" className="btn btn-outline" style={{ display: "inline-flex", alignItems: "center", gap: "0.5rem" }}>
            <ShieldCheck size={18} />
            Doctor Dashboard View
          </Link>
        </div>

        <p style={{ fontSize: "1.1rem", color: "var(--color-text-primary)", marginTop: "1.5rem", lineHeight: 1.6 }}>
          {parent_summary}
        </p>
      </div>

      {/* 2. Hero stats row */}
      <div className="grid-3">
        <StatCard
          icon={Award}
          label="Completion Rate"
          value={`${Math.round(session_summary.completion_rate * 100)}%`}
          subLabel={`${session_summary.levels_completed} of ${session_summary.levels_total} levels cleared`}
          iconColor="var(--color-success)"
        />
        <StatCard
          icon={Clock}
          label="Active Learning Time"
          value={`${session_summary.total_minutes} min`}
          subLabel="Non-stress screen pacing"
          iconColor="var(--color-primary)"
        />
        <StatCard
          icon={AlertTriangle}
          label="Struggle Replans"
          value={session_summary.replan_count}
          subLabel={session_summary.replan_count > 0 ? "Helped child past bottleneck" : "Steady attention"}
          iconColor="var(--color-accent)"
        />
      </div>

      {/* 3. Attention Arc Chart (Recharts) */}
      <div className="grid-2">
        <div className="card">
          <h2 style={{ fontSize: "1.25rem", fontWeight: "900", marginBottom: "1rem" }}>Attention Arc</h2>
          <p style={{ fontSize: "0.85rem", color: "var(--color-text-secondary)", marginBottom: "1rem" }}>
            Presents errors logged over the session. Notice how struggles are mitigated post-replan intervals.
          </p>
          <div className="chart-container">
            <AttentionArcChart data={attention_arc} />
          </div>
        </div>

        {/* Concept Performance Table */}
        <div className="card" style={{ display: "flex", flexDirection: "column" }}>
          <h2 style={{ fontSize: "1.25rem", fontWeight: "900", marginBottom: "1rem" }}>Concept Focus breakdown</h2>
          <div style={{ flex: 1, overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.95rem" }}>
              <thead>
                <tr style={{ borderBottom: "1px solid var(--color-border)", textAlign: "left" }}>
                  <th style={{ padding: "0.75rem 0.5rem", color: "var(--color-text-muted)" }}>CONCEPT</th>
                  <th style={{ padding: "0.75rem 0.5rem", color: "var(--color-text-muted)" }}>TIME SPENT</th>
                  <th style={{ padding: "0.75rem 0.5rem", color: "var(--color-text-muted)" }}>STRUGGLE INDEX</th>
                </tr>
              </thead>
              <tbody>
                {concept_performance.map((c) => {
                  let failIndicatorColor = "var(--color-success)";
                  if (c.fail_rate > 0.4) failIndicatorColor = "var(--color-danger)";
                  else if (c.fail_rate > 0) failIndicatorColor = "var(--color-accent)";

                  return (
                    <tr key={c.concept} style={{ borderBottom: "1px solid rgba(255,255,255,0.02)" }}>
                      <td style={{ padding: "0.75rem 0.5rem", fontWeight: "800", textTransform: "capitalize" }}>
                        {c.concept}
                      </td>
                      <td style={{ padding: "0.75rem 0.5rem", color: "var(--color-text-secondary)" }}>
                        {c.avg_time_seconds ? `${Math.round(c.avg_time_seconds / 60)}m ${c.avg_time_seconds % 60}s` : "N/A"}
                      </td>
                      <td style={{ padding: "0.75rem 0.5rem", display: "flex", alignItems: "center", gap: "0.5rem" }}>
                        <div style={{ width: "8px", height: "8px", borderRadius: "50%", backgroundColor: failIndicatorColor }} />
                        <span style={{ fontWeight: "700" }}>{Math.round(c.fail_rate * 100)}%</span>
                        {c.replan_triggered && <span className="role-badge parent" style={{ fontSize: "0.65rem", padding: "0.1rem 0.4rem" }}>replan</span>}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* 4. Action forms row: Share & Medication */}
      <div className="grid-2">
        {/* Next Session recommendations */}
        <div className="card" style={{ display: "flex", flexDirection: "column", justifySelf: "stretch" }}>
          <h2 style={{ fontSize: "1.25rem", fontWeight: "900", marginBottom: "1rem", display: "flex", alignItems: "center", gap: "0.5rem" }}>
            <Award size={20} color="var(--color-accent)" />
            Next Quest Plan
          </h2>
          <div style={{ display: "flex", flexDirection: "column", gap: "1rem", flex: 1 }}>
            <div>
              <span style={{ fontSize: "0.8rem", color: "var(--color-text-muted)", fontWeight: "700" }}>SUGGESTED PACING</span>
              <p style={{ fontSize: "1.1rem", fontWeight: "800" }}>{next_session_recommendations.suggested_duration_minutes} minutes maximum</p>
            </div>
            <div>
              <span style={{ fontSize: "0.8rem", color: "var(--color-text-muted)", fontWeight: "700" }}>CONCEPTS TO SOLIDIFY</span>
              <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap", marginTop: "0.25rem" }}>
                {next_session_recommendations.prioritize_concepts.map((concept) => (
                  <span key={concept} className="role-badge doctor" style={{ textTransform: "capitalize" }}>
                    {concept}
                  </span>
                ))}
              </div>
            </div>
            <div>
              <span style={{ fontSize: "0.8rem", color: "var(--color-text-muted)", fontWeight: "700" }}>WARMUP TOPIC</span>
              <p style={{ textTransform: "capitalize", fontWeight: "700" }}>{next_session_recommendations.start_with_concept}</p>
            </div>
          </div>
        </div>

        {/* Share with Clinical Specialist */}
        <div className="card" style={{ display: "flex", flexDirection: "column", justifySelf: "stretch" }}>
          <h2 style={{ fontSize: "1.25rem", fontWeight: "900", marginBottom: "1rem", display: "flex", alignItems: "center", gap: "0.5rem" }}>
            <Mail size={20} color="var(--color-primary)" />
            Share with Clinical Specialist
          </h2>
          <p style={{ fontSize: "0.85rem", color: "var(--color-text-secondary)", marginBottom: "1.25rem" }}>
            Input your child's pediatrician or therapist's email. This unlocks the clinical dashboard containing graph centrality bottlenecks for their assessment.
          </p>
          <form onSubmit={handleShare} style={{ display: "flex", gap: "0.5rem", marginTop: "auto" }}>
            <input
              type="email"
              className="form-input"
              placeholder="doctor@pediatrics.org"
              value={sharingEmail}
              onChange={(e) => setSharingEmail(e.target.value)}
              required
            />
            <button type="submit" className="btn btn-primary" disabled={shareLoading}>
              Share
            </button>
          </form>
        </div>
      </div>

      {/* 5. Medication correlation logger */}
      <div className="card">
        <h2 style={{ fontSize: "1.25rem", fontWeight: "900", marginBottom: "1rem", display: "flex", alignItems: "center", gap: "0.5rem" }}>
          <Heart size={20} color="var(--color-danger)" />
          Medication Tracking Log (Optional)
        </h2>
        <p style={{ fontSize: "0.85rem", color: "var(--color-text-secondary)", marginBottom: "1.25rem" }}>
          Log any medication taken before today's learning session. This logs the dosage delta to reveal focus trends over time on clinical graphs.
        </p>
        <form onSubmit={handleLogMed} style={{ display: "flex", flexWrap: "wrap", gap: "1rem", alignItems: "flex-end" }}>
          <div className="form-group" style={{ flex: 1, minWidth: "200px", marginBottom: 0 }}>
            <span className="form-label">Medication Name</span>
            <input
              type="text"
              className="form-input"
              placeholder="e.g. Methylphenidate"
              value={medName}
              onChange={(e) => setMedName(e.target.value)}
              required
            />
          </div>
          <div className="form-group" style={{ flex: 1, minWidth: "150px", marginBottom: 0 }}>
            <span className="form-label">Dosage (mg)</span>
            <input
              type="number"
              className="form-input"
              placeholder="e.g. 10"
              value={medDose}
              onChange={(e) => setMedDose(e.target.value)}
              required
            />
          </div>
          <button type="submit" className="btn btn-accent" disabled={medLoading} style={{ display: "flex", alignItems: "center", gap: "0.25rem", height: "46px" }}>
            <Plus size={16} />
            Log Dosage
          </button>
        </form>
      </div>

    </div>
  );
}
export default ParentReport;
