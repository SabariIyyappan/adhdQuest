import { useEffect, useState } from "react";
import type { ReplanEvent } from "@adhdquest/contracts";
import { Play, ArrowRight, Video } from "lucide-react";
import { motion } from "framer-motion";

interface ReplanOverlayProps {
  replan: ReplanEvent;
}

export function ReplanOverlay({ replan }: ReplanOverlayProps) {
  const [visible, setVisible] = useState(true);

  // Auto-dismiss after 8 seconds if there is no video, so it doesn't block the screen indefinitely
  useEffect(() => {
    if (replan.video) return;
    const t = setTimeout(() => setVisible(false), 8000);
    return () => clearTimeout(t);
  }, [replan]);

  if (!visible) return null;

  return (
    <div className="replan-backdrop">
      <motion.div
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.9, opacity: 0 }}
        className="replan-card"
      >
        <div style={{ display: "flex", justifyContent: "center", marginBottom: "0.5rem" }}>
          <div style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            width: "48px",
            height: "48px",
            borderRadius: "50%",
            backgroundColor: "rgba(253, 203, 110, 0.15)",
            color: "var(--color-accent)",
          }}>
            <Video size={24} />
          </div>
        </div>

        <h3 className="replan-title">Let's take a quick breather!</h3>
        <p className="replan-desc">{replan.explanation}</p>

        {replan.video && (
          <div className="video-container">
            <div
              className="video-thumbnail-wrapper"
              onClick={() => window.open(replan.video?.url, "_blank")}
              style={{
                backgroundImage: `linear-gradient(rgba(0,0,0,0.2), rgba(0,0,0,0.5)), url(${replan.video.thumbnail_url})`
              }}
            >
              <button className="video-play-btn">
                <Play size={20} fill="#fff" />
              </button>
              <span className="video-duration">
                {Math.round(replan.video.duration_seconds / 60)} min
              </span>
            </div>
            <div className="video-info">
              <span className="video-concept">EXPLANATION VIDEO</span>
              <h4 className="video-title">{replan.video.title}</h4>
            </div>
          </div>
        )}

        <div className="replan-actions">
          {replan.video && (
            <a
              href={replan.video.url}
              target="_blank"
              rel="noreferrer"
              className="btn btn-primary"
              style={{ display: "inline-flex", alignItems: "center", gap: "0.5rem" }}
            >
              Watch Video
              <ArrowRight size={16} />
            </a>
          )}
          <button
            onClick={() => setVisible(false)}
            className="btn btn-outline"
          >
            {replan.video ? "Skip to Game" : "Got it!"}
          </button>
        </div>
      </motion.div>
    </div>
  );
}
