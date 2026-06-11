import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import type { PortfolioSummary } from "../types/portfolio";
import { STAGE_LABELS } from "../types/portfolio";

const STAGE_COLORS: Record<string, string> = {
  stage_1: "#15803d",
  stage_2: "#b45309",
  stage_3: "#b91c1c",
};

interface Props {
  summary: PortfolioSummary;
}

export function StageBreakdownChart({ summary }: Props) {
  const data = (Object.keys(summary.by_stage) as Array<keyof typeof summary.by_stage>).map((stage) => ({
    stage: STAGE_LABELS[stage],
    "Loan Count": summary.by_stage[stage].loan_count,
    color: STAGE_COLORS[stage],
  }));

  return (
    <div className="chart-card">
      <h3>Loans by Stage</h3>
      <ResponsiveContainer width="100%" height={260}>
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" vertical={false} />
          <XAxis dataKey="stage" />
          <YAxis allowDecimals={false} />
          <Tooltip />
          <Bar dataKey="Loan Count" radius={[4, 4, 0, 0]}>
            {data.map((entry) => (
              <Cell key={entry.stage} fill={entry.color} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
