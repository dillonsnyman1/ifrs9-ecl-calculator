import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import type { PortfolioSummary } from "../types/portfolio";
import { STAGE_LABELS } from "../types/portfolio";

const currencyFormatter = new Intl.NumberFormat("en-GB", {
  style: "currency",
  currency: "GBP",
  maximumFractionDigits: 0,
});

interface Props {
  summary: PortfolioSummary;
}

export function EclByStageChart({ summary }: Props) {
  const data = (Object.keys(summary.by_stage) as Array<keyof typeof summary.by_stage>).map((stage) => ({
    stage: STAGE_LABELS[stage],
    "ECL (discounted)": Math.round(summary.by_stage[stage].ecl),
    "ECL (undiscounted)": Math.round(summary.by_stage[stage].ecl_undiscounted),
  }));

  return (
    <div className="chart-card">
      <h3>ECL by Stage</h3>
      <ResponsiveContainer width="100%" height={260}>
        <BarChart data={data} margin={{ left: 10 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="stage" />
          <YAxis width={80} tickFormatter={(value) => currencyFormatter.format(value as number)} />
          <Tooltip formatter={(value) => currencyFormatter.format(Number(value))} />
          <Legend />
          <Bar dataKey="ECL (discounted)" fill="#b91c1c" radius={[4, 4, 0, 0]} />
          <Bar dataKey="ECL (undiscounted)" fill="#fca5a5" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
