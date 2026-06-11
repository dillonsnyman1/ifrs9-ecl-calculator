// free text portfolio segment, e.g. "personal_loan", "sme_term_loans" - whatever
// the uploaded portfolio uses
export type ProductType = string;

export type Stage = "stage_1" | "stage_2" | "stage_3";

export type DiscountMethod = "midpoint" | "end_of_horizon";

export interface Loan {
  loan_id: string;
  product_type: ProductType;
  exposure_at_default: number;
  lgd: number;
  pd_12m: number;
  pd_origination: number;
  days_past_due: number;
  remaining_term_months: number;
  eir: number;
}

export interface ProcessedLoan extends Loan {
  stage: Stage;
  pd_lifetime: number;
  ecl: number;
  ecl_undiscounted: number;
}

export interface StageSummary {
  loan_count: number;
  exposure: number;
  ecl: number;
  ecl_undiscounted: number;
}

export interface PortfolioSummary {
  loan_count: number;
  total_exposure: number;
  total_ecl: number;
  total_ecl_undiscounted: number;
  coverage_ratio: number;
  by_stage: Record<Stage, StageSummary>;
}

export interface PortfolioResponse {
  loans: ProcessedLoan[];
  summary: PortfolioSummary;
}

export const STAGE_LABELS: Record<Stage, string> = {
  stage_1: "Stage 1",
  stage_2: "Stage 2",
  stage_3: "Stage 3",
};

// portfolio segments are free text (e.g. "personal_loan"), so just turn
// underscores into spaces and title-case it for display
export function formatProductType(productType: string): string {
  return productType
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

export const DISCOUNT_METHOD_LABELS: Record<DiscountMethod, string> = {
  midpoint: "Midpoint of horizon",
  end_of_horizon: "End of horizon",
};
