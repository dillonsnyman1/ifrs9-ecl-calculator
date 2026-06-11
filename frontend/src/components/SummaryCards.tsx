import type { PortfolioSummary } from "../types/portfolio";

const currencyFormatter = new Intl.NumberFormat("en-GB", {
  style: "currency",
  currency: "GBP",
  maximumFractionDigits: 0,
});

const percentFormatter = new Intl.NumberFormat("en-GB", {
  style: "percent",
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

interface Props {
  summary: PortfolioSummary;
}

export function SummaryCards({ summary }: Props) {
  const cards = [
    {
      label: "Number of Loans",
      value: summary.loan_count.toLocaleString(),
      accent: "#2563eb",
    },
    {
      label: "Total Exposure (EAD)",
      value: currencyFormatter.format(summary.total_exposure),
      accent: "#2563eb",
    },
    {
      label: "Total ECL (discounted)",
      value: currencyFormatter.format(summary.total_ecl),
      sub: `${currencyFormatter.format(summary.total_ecl_undiscounted)} undiscounted`,
      accent: "#b91c1c",
    },
    {
      label: "ECL Coverage Ratio",
      value: percentFormatter.format(summary.coverage_ratio),
      accent: "#15803d",
    },
  ];

  return (
    <div className="summary-cards">
      {cards.map((card) => (
        <div className="summary-card" key={card.label} style={{ borderTopColor: card.accent }}>
          <div className="summary-card-label">{card.label}</div>
          <div className="summary-card-value">{card.value}</div>
          {card.sub && <div className="summary-card-subvalue">{card.sub}</div>}
        </div>
      ))}
    </div>
  );
}
