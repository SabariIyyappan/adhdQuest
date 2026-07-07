/** Attention arc — errors over session time (Contract E attention_arc). */

import { CartesianGrid, Line, LineChart, ResponsiveContainer, XAxis, YAxis } from "recharts";
import type { AttentionArcPoint } from "@adhdquest/contracts";

export function AttentionArcChart({ data }: { data: AttentionArcPoint[] }) {
  return (
    <ResponsiveContainer width="100%" height={220}>
      <LineChart data={data}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="minute" unit="m" />
        <YAxis allowDecimals={false} />
        <Line type="monotone" dataKey="errors" stroke="#6c5ce7" dot={false} />
      </LineChart>
    </ResponsiveContainer>
  );
}
