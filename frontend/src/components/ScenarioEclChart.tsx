import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import type { PortfolioSummary } from "../types/portfolio";
import { SCENARIO_LABELS } from "../types/portfolio";

const currencyFormatter = new Intl.NumberFormat("en-GB", {
  style: "currency",
  currency: "GBP",
  maximumFractionDigits: 0,
});

interface Props {
  summary: PortfolioSummary;
}

export function ScenarioEclChart({ summary }: Props) {
  const data = (Object.keys(summary.by_scenario) as Array<keyof typeof summary.by_scenario>).map((scenario) => ({
    scenario: SCENARIO_LABELS[scenario],
    "Scenario ECL (discounted)": Math.round(summary.by_scenario[scenario].ecl),
  }));

  data.push({
    scenario: "Probability-weighted",
    "Scenario ECL (discounted)": Math.round(summary.total_ecl),
  });

  return (
    <div className="chart-card">
      <h3>ECL by Macroeconomic Scenario</h3>
      <ResponsiveContainer width="100%" height={260}>
        <BarChart data={data} margin={{ left: 10 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="scenario" />
          <YAxis width={80} tickFormatter={(value) => currencyFormatter.format(value as number)} />
          <Tooltip formatter={(value) => currencyFormatter.format(Number(value))} />
          <Legend />
          <Bar dataKey="Scenario ECL (discounted)" fill="#7c3aed" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
