import { Bar, BarChart, CartesianGrid, ResponsiveContainer, XAxis, YAxis, Tooltip } from "recharts";

interface ConceptBottleneckPoint {
  concept: string;
  centrality: number;
}

export function ConceptBottleneckChart({ data }: { data: ConceptBottleneckPoint[] }) {
  const sortedData = [...data].sort((a, b) => b.centrality - a.centrality);

  return (
    <ResponsiveContainer width="100%" height={220}>
      <BarChart data={sortedData} layout="vertical" margin={{ left: 20, right: 20 }}>
        <CartesianGrid strokeDasharray="3 3" horizontal={false} />
        <XAxis type="number" domain={[0, 1]} stroke="var(--color-text-secondary)" />
        <YAxis dataKey="concept" type="category" stroke="var(--color-text-secondary)" width={80} style={{ textTransform: "capitalize", fontWeight: "700" }} />
        <Tooltip
          contentStyle={{ backgroundColor: "var(--color-surface)", borderColor: "var(--color-border)" }}
          labelStyle={{ color: "var(--color-text-primary)" }}
        />
        <Bar dataKey="centrality" fill="var(--color-accent)" radius={[0, 4, 4, 0]} barSize={16} />
      </BarChart>
    </ResponsiveContainer>
  );
}
