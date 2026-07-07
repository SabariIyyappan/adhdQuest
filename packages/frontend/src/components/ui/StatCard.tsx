import type { LucideIcon } from "lucide-react";

interface StatCardProps {
  icon: LucideIcon;
  value: string | number;
  label: string;
  subLabel?: string;
  iconColor?: string;
  accentColor?: string;
}

export function StatCard({
  icon: Icon,
  value,
  label,
  subLabel,
  iconColor = "var(--color-primary)",
  accentColor = "var(--color-border)",
}: StatCardProps) {
  return (
    <div
      className="card animate-slide-in"
      style={{
        display: "flex",
        alignItems: "center",
        gap: "1.25rem",
        padding: "1.25rem",
        borderLeft: `4px solid ${iconColor}`,
        borderColor: accentColor,
      }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          width: "48px",
          height: "48px",
          borderRadius: "12px",
          backgroundColor: `rgba(255, 255, 255, 0.05)`,
          color: iconColor,
        }}
      >
        <Icon size={24} />
      </div>
      <div style={{ display: "flex", flexDirection: "column", flex: 1, gap: "0.25rem" }}>
        <span style={{ fontSize: "0.85rem", fontWeight: "700", color: "var(--color-text-secondary)", textTransform: "uppercase", letterSpacing: "0.05em" }}>
          {label}
        </span>
        <span style={{ fontSize: "1.75rem", fontWeight: "900", color: "var(--color-text-primary)", lineHeight: 1.1 }}>
          {value}
        </span>
        {subLabel && (
          <span style={{ fontSize: "0.75rem", color: "var(--color-text-muted)", fontWeight: "600" }}>
            {subLabel}
          </span>
        )}
      </div>
    </div>
  );
}
