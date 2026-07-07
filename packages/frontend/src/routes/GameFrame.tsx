/**
 * Game frame — embeds the Daytona preview URL and reacts to realtime session events:
 * shows the replan overlay + video, and transitions to the report on session end.
 */

import { useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useSession } from "../hooks/useSession";
import { ReplanOverlay } from "../components/ReplanOverlay";

export function GameFrame() {
  const { childId = "" } = useParams();
  const { gameUrl, levelCount, replan, reportId } = useSession(childId);
  const navigate = useNavigate();

  useEffect(() => {
    if (reportId) navigate(`/report/${reportId}`);
  }, [reportId, navigate]);

  if (!gameUrl) return <p>Generating your game…</p>;

  return (
    <div className="game-frame">
      <iframe title="ADHDQuest game" src={gameUrl} allow="autoplay; fullscreen" />
      <aside className="game-sidebar">
        <p>Levels: {levelCount}</p>
        {/* progress bar / non-alarming streak indicator */}
      </aside>
      {replan && <ReplanOverlay replan={replan} />}
    </div>
  );
}
