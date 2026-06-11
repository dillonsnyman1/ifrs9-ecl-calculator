import { useMemo, useState } from "react";

import type { ProcessedLoan, ProductType, Stage } from "../types/portfolio";
import { formatProductType, STAGE_LABELS } from "../types/portfolio";

const currencyFormatter = new Intl.NumberFormat("en-GB", {
  style: "currency",
  currency: "GBP",
  maximumFractionDigits: 2,
});

const percentFormatter = new Intl.NumberFormat("en-GB", {
  style: "percent",
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

type SortKey = keyof Pick<
  ProcessedLoan,
  | "loan_id"
  | "product_type"
  | "exposure_at_default"
  | "lgd"
  | "pd_12m"
  | "pd_lifetime"
  | "eir"
  | "stage"
  | "ecl"
  | "ecl_undiscounted"
>;

interface Column {
  key: string;
  label: string;
  sortKey?: SortKey;
  render: (loan: ProcessedLoan) => React.ReactNode;
}

function eclBasis(loan: ProcessedLoan): string {
  return loan.stage === "stage_1" ? "12-month" : "Lifetime";
}

const COLUMNS: Column[] = [
  { key: "loan_id", label: "Loan ID", sortKey: "loan_id", render: (l) => l.loan_id },
  { key: "product_type", label: "Portfolio", sortKey: "product_type", render: (l) => formatProductType(l.product_type) },
  { key: "exposure_at_default", label: "EAD", sortKey: "exposure_at_default", render: (l) => currencyFormatter.format(l.exposure_at_default) },
  { key: "lgd", label: "LGD", sortKey: "lgd", render: (l) => percentFormatter.format(l.lgd) },
  { key: "pd_12m", label: "12m PD", sortKey: "pd_12m", render: (l) => percentFormatter.format(l.pd_12m) },
  { key: "pd_lifetime", label: "Lifetime PD", sortKey: "pd_lifetime", render: (l) => percentFormatter.format(l.pd_lifetime) },
  { key: "eir", label: "EIR", sortKey: "eir", render: (l) => percentFormatter.format(l.eir) },
  {
    key: "stage",
    label: "Stage",
    sortKey: "stage",
    render: (l) => <span className={`stage-badge ${l.stage}`}>{STAGE_LABELS[l.stage]}</span>,
  },
  { key: "ecl_basis", label: "ECL Basis", render: eclBasis },
  { key: "ecl", label: "ECL (discounted)", sortKey: "ecl", render: (l) => currencyFormatter.format(l.ecl) },
  {
    key: "ecl_undiscounted",
    label: "ECL (undiscounted)",
    sortKey: "ecl_undiscounted",
    render: (l) => currencyFormatter.format(l.ecl_undiscounted),
  },
];

interface Props {
  loans: ProcessedLoan[];
}

export function LoanTable({ loans }: Props) {
  const [stageFilter, setStageFilter] = useState<Stage | "all">("all");
  const [productFilter, setProductFilter] = useState<ProductType | "all">("all");
  const [sortKey, setSortKey] = useState<SortKey>("loan_id");
  const [sortDir, setSortDir] = useState<"asc" | "desc">("asc");

  const productTypes = useMemo(() => {
    return Array.from(new Set(loans.map((loan) => loan.product_type))).sort();
  }, [loans]);

  const filtered = useMemo(() => {
    return loans.filter((loan) => {
      if (stageFilter !== "all" && loan.stage !== stageFilter) return false;
      if (productFilter !== "all" && loan.product_type !== productFilter) return false;
      return true;
    });
  }, [loans, stageFilter, productFilter]);

  const sorted = useMemo(() => {
    const copy = [...filtered];
    copy.sort((a, b) => {
      const aVal = a[sortKey];
      const bVal = b[sortKey];
      const cmp =
        typeof aVal === "number" && typeof bVal === "number" ? aVal - bVal : String(aVal).localeCompare(String(bVal));
      return sortDir === "asc" ? cmp : -cmp;
    });
    return copy;
  }, [filtered, sortKey, sortDir]);

  function handleSort(key: SortKey) {
    if (key === sortKey) {
      setSortDir((dir) => (dir === "asc" ? "desc" : "asc"));
    } else {
      setSortKey(key);
      setSortDir("asc");
    }
  }

  return (
    <div className="loan-table-card">
      <h3>Loan Detail</h3>
      <div className="loan-table-controls">
        <label>
          Stage
          <select value={stageFilter} onChange={(e) => setStageFilter(e.target.value as Stage | "all")}>
            <option value="all">All</option>
            {(Object.keys(STAGE_LABELS) as Stage[]).map((stage) => (
              <option key={stage} value={stage}>
                {STAGE_LABELS[stage]}
              </option>
            ))}
          </select>
        </label>
        <label>
          Portfolio
          <select value={productFilter} onChange={(e) => setProductFilter(e.target.value as ProductType | "all")}>
            <option value="all">All</option>
            {productTypes.map((product) => (
              <option key={product} value={product}>
                {formatProductType(product)}
              </option>
            ))}
          </select>
        </label>
        <span className="loan-table-count">{sorted.length} loans</span>
      </div>

      <div className="loan-table-scroll">
        <table className="loan-table">
          <thead>
            <tr>
              {COLUMNS.map((col) => (
                <th
                  key={col.key}
                  onClick={col.sortKey ? () => handleSort(col.sortKey as SortKey) : undefined}
                  className={col.sortKey ? undefined : "not-sortable"}
                >
                  {col.label}
                  {col.sortKey && sortKey === col.sortKey ? (sortDir === "asc" ? " ▲" : " ▼") : ""}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {sorted.map((loan) => (
              <tr key={loan.loan_id}>
                {COLUMNS.map((col) => (
                  <td key={col.key}>{col.render(loan)}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
