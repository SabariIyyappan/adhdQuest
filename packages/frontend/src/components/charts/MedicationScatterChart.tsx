import { ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";

interface ScatterPoint {
  timeDeltaMinutes: number; // minutes since medication
  attentionWindow: number;  // attention baseline/performance minutes
}

export function MedicationScatterChart({ data }: { data: ScatterPoint[] }) {
  return (
    <ResponsiveContainer width="100%" height={220}>
      <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis
          type="number"
          dataKey="timeDeltaMinutes"
          name="Time Since Dose"
          unit="m"
          label={{ value: "Time since dose (min)", position: "bottom", fill: "var(--color-text-secondary)", offset: 0 }}
          stroke="var(--color-text-secondary)"
        />
        <YAxis
          type="number"
          dataKey="attentionWindow"
          name="Attention Span"
          unit="m"
          label={{ value: "Attention span (min)", angle: -90, position: "left", fill: "var(--color-text-secondary)", offset: 10 }}
          stroke="var(--color-text-secondary)"
        />
        <Tooltip
          cursor={{ strokeDasharray: "3 3" }}
          contentStyle={{ backgroundColor: "var(--color-surface)", borderColor: "var(--color-border)" }}
          labelStyle={{ color: "var(--color-text-primary)" }}
        />
        <Scatter name="Attention vs Medication" data={data} fill="var(--color-danger)" />
      </ScatterChart>
    </ResponsiveContainer>
  );
}
