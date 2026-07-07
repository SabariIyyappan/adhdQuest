import { motion } from "framer-motion";

interface ProgressBarProps {
  value: number; // 0 to 100
  label?: string;
  color?: string; // CSS color string or default variables
  showPercent?: boolean;
}

export function ProgressBar({ value, label, color = "var(--color-primary)", showPercent = false }: ProgressBarProps) {
  const clampedValue = Math.min(100, Math.max(0, value));

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem", width: "100%" }}>
      {(label || showPercent) && (
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", fontSize: "0.9rem", fontWeight: "700" }}>
          {label && <span style={{ color: "var(--color-text-secondary)" }}>{label}</span>}
          {showPercent && <span style={{ color: "var(--color-text-primary)" }}>{Math.round(clampedValue)}%</span>}
        </div>
      )}
      <div
        style={{
          width: "100%",
          height: "12px",
          backgroundColor: "var(--color-bg)",
          borderRadius: "9999px",
          overflow: "hidden",
          border: "1px solid var(--color-border)",
        }}
      >
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${clampedValue}%` }}
          transition={{ duration: 0.5, ease: "easeOut" }}
          style={{
            height: "100%",
            backgroundColor: color,
            borderRadius: "9999px",
          }}
        />
      </div>
    </div>
  );
}
