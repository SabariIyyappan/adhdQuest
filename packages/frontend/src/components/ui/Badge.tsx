import { motion } from "framer-motion";

interface BadgeProps {
  label: string;
  subLabel?: string;
  icon?: string; // emoji icon or character
  unlocked?: boolean;
}

export function Badge({ label, subLabel, icon = "🌟", unlocked = true }: BadgeProps) {
  return (
    <motion.div
      whileHover={unlocked ? { scale: 1.08, rotate: [0, -5, 5, 0] } : {}}
      transition={{ type: "spring", stiffness: 300, damping: 15 }}
      style={{
        display: "flex",
        alignItems: "center",
        gap: "0.75rem",
        padding: "0.75rem 1rem",
        borderRadius: "16px",
        backgroundColor: unlocked ? "rgba(253, 203, 110, 0.1)" : "rgba(255, 255, 255, 0.02)",
        border: `2px dashed ${unlocked ? "var(--color-accent)" : "var(--color-border)"}`,
        opacity: unlocked ? 1 : 0.4,
        cursor: unlocked ? "pointer" : "not-allowed",
        transition: "border-color 0.2s, background-color 0.2s",
      }}
    >
      <span style={{ fontSize: "1.75rem", filter: unlocked ? "none" : "grayscale(100%)" }}>{icon}</span>
      <div style={{ display: "flex", flexDirection: "column" }}>
        <span style={{ fontSize: "0.9rem", fontWeight: "800", color: unlocked ? "var(--color-text-primary)" : "var(--color-text-muted)" }}>
          {label}
        </span>
        {subLabel && (
          <span style={{ fontSize: "0.7rem", color: "var(--color-text-secondary)", fontWeight: "600" }}>
            {subLabel}
          </span>
        )}
      </div>
    </motion.div>
  );
}
