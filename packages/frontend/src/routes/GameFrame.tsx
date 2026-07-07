import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useSession } from "../hooks/useSession";
import { ReplanOverlay } from "../components/ReplanOverlay";
import { ProgressBar } from "../components/ui/ProgressBar";
import { Badge } from "../components/ui/Badge";
import { useToast } from "../components/ui/ToastProvider";
import { Trophy, Clock, Target, AlertCircle } from "lucide-react";
import { LoadingSkeleton } from "../components/ui/LoadingSkeleton";

export function GameFrame() {
  const { childId = "" } = useParams();
  const { gameUrl, levelCount, currentLevelIndex, replan, reportId } = useSession(childId);
  const navigate = useNavigate();
  const { info, success } = useToast();
  
  const [secondsElapsed, setSecondsElapsed] = useState(0);
  const [xp, setXp] = useState(0);
  const [streak, setStreak] = useState(0);

  // Expose local simulation for the demo if gameUrl is a mockup
  const isMockApp = !gameUrl || gameUrl.includes("mock");

  // Track session duration
  useEffect(() => {
    const interval = setInterval(() => {
      setSecondsElapsed((prev) => prev + 1);
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  // Sync rewards and notify on level changes
  useEffect(() => {
    if (currentLevelIndex > 1) {
      setXp((prev) => prev + 50);
      setStreak((prev) => prev + 1);
      success(`Level ${currentLevelIndex - 1} Complete! +50 XP 🌟`);
    }
  }, [currentLevelIndex, success]);

  // Route to report when session ends
  useEffect(() => {
    if (reportId) {
      success("Session complete! Compiling insights report...");
      navigate(`/report/${reportId}`);
    }
  }, [reportId, navigate, success]);

  // Trigger toast on replan
  useEffect(() => {
    if (replan) {
      info("Adapting game content: adding prerequisite explanation step.", 5000);
    }
  }, [replan, info]);

  // Render format time
  const formatTime = (secs: number) => {
    const mins = Math.floor(secs / 60);
    const remainingSecs = secs % 60;
    return `${mins}:${remainingSecs < 10 ? "0" : ""}${remainingSecs}`;
  };

  // Safe Fallback URL if we are in mockup mode
  const resolvedGameUrl = gameUrl || "https://daytona.butterbase.dev/mock-pygame-canvas";

  // Simulate event helper for local sandbox debugging
  const triggerSimulatedComplete = () => {
    window.postMessage({ type: "level_complete", level: currentLevelIndex + 1 }, "*");
  };


  const triggerSimulatedEnd = () => {
    // Redirect to parent report with a mock report id
    navigate("/report/report_demo_1");
  };

  if (!gameUrl && !isMockApp) {
    return (
      <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem", padding: "3rem", maxWidth: "600px", margin: "10% auto" }}>
        <h2 style={{ fontWeight: "900", textAlign: "center" }}>Setting up Sandbox...</h2>
        <LoadingSkeleton height={30} />
        <p style={{ color: "var(--color-text-secondary)", textAlign: "center" }}>
          Daytona is booting your safe environment & compiling your personalized Python game.
        </p>
        <LoadingSkeleton height={15} />
        <LoadingSkeleton height={15} />
      </div>
    );
  }

  // Calculate progress percentage
  const totalLevels = levelCount || 8;
  const progressPercent = ((currentLevelIndex - 1) / totalLevels) * 100;

  return (
    <div className="game-layout">
      {/* 1. Main Game Frame Area */}
      <div className="game-main">
        {/* Replan overlay rendered over the game frame if active */}
        {replan && <ReplanOverlay replan={replan} />}

        <iframe
          title="ADHDQuest game"
          src={resolvedGameUrl}
          className="game-iframe"
          allow="autoplay; fullscreen"
        />

        {/* Demo Simulation Controls for developer evaluation */}
        {isMockApp && (
          <div style={{
            position: "absolute",
            bottom: "1rem",
            left: "1rem",
            backgroundColor: "var(--color-surface)",
            padding: "0.75rem",
            borderRadius: "12px",
            border: "1px solid var(--color-border)",
            display: "flex",
            gap: "0.5rem",
            boxShadow: "0 4px 10px rgba(0,0,0,0.3)"
          }}>
            <button className="btn btn-outline" style={{ padding: "0.4rem 0.8rem", fontSize: "0.75rem" }} onClick={triggerSimulatedComplete}>
              Simulate Complete Level
            </button>
            <button className="btn btn-outline" style={{ padding: "0.4rem 0.8rem", fontSize: "0.75rem", borderColor: "var(--color-accent)", color: "var(--color-accent)" }} onClick={triggerSimulatedEnd}>
              Simulate Session End
            </button>
          </div>
        )}
      </div>

      {/* 2. Interactive ADHD Sidebar */}
      <aside className="game-sidebar">
        <div className="sidebar-header">
          <h2 style={{ fontSize: "1.25rem", fontWeight: "900", display: "flex", alignItems: "center", gap: "0.5rem" }}>
            <Trophy color="var(--color-accent)" size={20} />
            Your Quest Tracker
          </h2>
        </div>

        {/* Level Progression */}
        <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
          <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.85rem", fontWeight: "800", color: "var(--color-text-secondary)" }}>
            <span>PROGRESS</span>
            <span>Level {currentLevelIndex} of {totalLevels}</span>
          </div>
          <ProgressBar value={progressPercent} color="var(--color-success)" />
        </div>

        {/* Real-time stats */}
        <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
          <div style={{ display: "flex", gap: "0.5rem", alignItems: "center", backgroundColor: "rgba(255,255,255,0.02)", border: "1px solid var(--color-border)", padding: "0.75rem", borderRadius: "12px" }}>
            <Clock size={16} color="var(--color-primary)" />
            <div style={{ display: "flex", flexDirection: "column" }}>
              <span style={{ fontSize: "0.7rem", color: "var(--color-text-muted)", fontWeight: "700" }}>TIME ELAPSED</span>
              <span style={{ fontSize: "1rem", fontWeight: "800" }}>{formatTime(secondsElapsed)}</span>
            </div>
          </div>

          <div style={{ display: "flex", gap: "0.5rem", alignItems: "center", backgroundColor: "rgba(255,255,255,0.02)", border: "1px solid var(--color-border)", padding: "0.75rem", borderRadius: "12px" }}>
            <Target size={16} color="var(--color-success)" />
            <div style={{ display: "flex", flexDirection: "column" }}>
              <span style={{ fontSize: "0.7rem", color: "var(--color-text-muted)", fontWeight: "700" }}>TOTAL SCORE</span>
              <span style={{ fontSize: "1rem", fontWeight: "800" }}>{xp} XP</span>
            </div>
          </div>
        </div>

        {/* Badge list */}
        <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
          <span style={{ fontSize: "0.75rem", color: "var(--color-text-muted)", fontWeight: "700", textTransform: "uppercase" }}>Unlocked Achievements</span>
          <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
            <Badge label="Fast Starter" subLabel="Completed Level 1 in under 1 min" icon="⚡" unlocked={currentLevelIndex > 1} />
            <Badge label="Three-in-a-row" subLabel="Correct answers streak bonus" icon="🔥" unlocked={streak >= 3} />
            <Badge label="Division Scholar" subLabel="Cleared division quest" icon="🧠" unlocked={currentLevelIndex > 4} />
          </div>
        </div>

        {/* ADHD friendly reminder */}
        <div style={{
          backgroundColor: "rgba(108, 92, 231, 0.05)",
          padding: "0.75rem 1rem",
          borderRadius: "12px",
          border: "1px solid rgba(108, 92, 231, 0.15)",
          marginTop: "auto",
          fontSize: "0.75rem",
          color: "var(--color-text-secondary)",
          lineHeight: 1.4,
          display: "flex",
          gap: "0.5rem"
        }}>
          <AlertCircle size={14} color="var(--color-primary)" style={{ flexShrink: 0 }} />
          <span>If you get stuck, the system will adjust the mechanics and offer video helpers. Breathe and have fun!</span>
        </div>
      </aside>
    </div>
  );
}
export default GameFrame;
