import { CartesianGrid, Line, LineChart, ResponsiveContainer, XAxis, YAxis, Tooltip, Legend } from "recharts";

interface AttentionArcPoint {
  minute: number;
  errors: number;
}

interface MultiSessionProps {
  sessions: {
    id: string;
    label: string;
    points: AttentionArcPoint[];
  }[];
}

export function MultiSessionAttentionChart({ sessions }: MultiSessionProps) {
  // Combine session curves into a unified chart layout
  // Find the maximum minute across all points
  const maxMinute = Math.max(...sessions.flatMap((s) => s.points.map((p) => p.minute)));
  
  // Construct data matrix where each minute lists error counts for each session
  const data = Array.from({ length: Math.ceil(maxMinute / 2) + 1 }, (_, index) => {
    const minute = index * 2;
    const item: any = { minute };
    sessions.forEach((s) => {
      const match = s.points.find((p) => p.minute === minute);
      if (match) item[s.label] = match.errors;
    });
    return item;
  });

  const colors = ["#6c5ce7", "#fdcb6e", "#00b894", "#e17055", "#9b59b6", "#3498db", "#e74c3c", "#2ecc71"];

  return (
    <ResponsiveContainer width="100%" height={220}>
      <LineChart data={data}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="minute" unit="m" stroke="var(--color-text-secondary)" />
        <YAxis allowDecimals={false} label={{ value: "Errors", angle: -90, position: "insideLeft", fill: "var(--color-text-secondary)" }} stroke="var(--color-text-secondary)" />
        <Tooltip
          contentStyle={{ backgroundColor: "var(--color-surface)", borderColor: "var(--color-border)" }}
          labelStyle={{ color: "var(--color-text-primary)" }}
        />
        <Legend />
        {sessions.map((s, idx) => (
          <Line
            key={s.id}
            type="monotone"
            dataKey={s.label}
            stroke={colors[idx % colors.length]}
            strokeWidth={2}
            dot={false}
            connectNulls
          />
        ))}
      </LineChart>
    </ResponsiveContainer>
  );
}
