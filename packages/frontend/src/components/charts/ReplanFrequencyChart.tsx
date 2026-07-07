import { Bar, BarChart, CartesianGrid, ResponsiveContainer, XAxis, YAxis, Tooltip } from "recharts";

interface ReplanFreqPoint {
  sessionName: string;
  replans: number;
}

export function ReplanFrequencyChart({ data }: { data: ReplanFreqPoint[] }) {
  return (
    <ResponsiveContainer width="100%" height={220}>
      <BarChart data={data}>
        <CartesianGrid strokeDasharray="3 3" vertical={false} />
        <XAxis dataKey="sessionName" stroke="var(--color-text-secondary)" />
        <YAxis allowDecimals={false} stroke="var(--color-text-secondary)" />
        <Tooltip
          contentStyle={{ backgroundColor: "var(--color-surface)", borderColor: "var(--color-border)" }}
          labelStyle={{ color: "var(--color-text-primary)" }}
        />
        <Bar dataKey="replans" fill="var(--color-primary)" radius={[4, 4, 0, 0]} barSize={24} />
      </BarChart>
    </ResponsiveContainer>
  );
}
