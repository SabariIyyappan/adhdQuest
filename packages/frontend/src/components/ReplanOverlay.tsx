/** "Adjusting your game…" overlay with the YouTube micro-lesson card (Contract C replan). */

import { useEffect, useState } from "react";
import type { ReplanEvent } from "@adhdquest/contracts";

export function ReplanOverlay({ replan }: { replan: ReplanEvent }) {
  const [visible, setVisible] = useState(true);

  // Auto-dismiss after 5s if there is no video to watch (plan §7 Person C).
  useEffect(() => {
    if (replan.video) return;
    const t = setTimeout(() => setVisible(false), 5000);
    return () => clearTimeout(t);
  }, [replan]);

  if (!visible) return null;

  return (
    <div className="replan-overlay" role="status">
      <p>{replan.explanation}</p>
      {replan.video && (
        <a className="video-card" href={replan.video.url} target="_blank" rel="noreferrer">
          <img src={replan.video.thumbnail_url} alt="" />
          <span>{replan.video.title}</span>
          <span>{Math.round(replan.video.duration_seconds / 60)} min</span>
        </a>
      )}
      <button onClick={() => setVisible(false)}>Continue</button>
    </div>
  );
}
