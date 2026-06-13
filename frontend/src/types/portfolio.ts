// free text portfolio segment, e.g. "personal_loan", "sme_term_loans" - whatever
// the uploaded portfolio uses
export type ProductType = string;

export type Stage = "stage_1" | "stage_2" | "stage_3";

export type DiscountMethod = "midpoint" | "end_of_horizon";

export type ScenarioName = "base" | "upside" | "downside";

export type StagingBasis = "base_case" | "scenario_weighted";

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
  ecl_scenarios: Record<ScenarioName, number>;
  ecl_undiscounted_scenarios: Record<ScenarioName, number>;
}

export interface StageSummary {
  loan_count: number;
  exposure: number;
  ecl: number;
  ecl_undiscounted: number;
}

export interface ScenarioSummary {
  ecl: number;
  ecl_undiscounted: number;
  coverage_ratio: number;
}

export interface PortfolioSummary {
  loan_count: number;
  total_exposure: number;
  total_ecl: number;
  total_ecl_undiscounted: number;
  coverage_ratio: number;
  by_stage: Record<Stage, StageSummary>;
  by_scenario: Record<ScenarioName, ScenarioSummary>;
  staging_basis: StagingBasis;
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

export interface StagingAssumptions {
  sicr_pd_multiple: number;
  stage_2_dpd_threshold: number;
  stage_3_dpd_threshold: number;
}

export const DEFAULT_STAGING_ASSUMPTIONS: StagingAssumptions = {
  sicr_pd_multiple: 2.0,
  stage_2_dpd_threshold: 30,
  stage_3_dpd_threshold: 90,
};

export interface ScenarioDefinition {
  weight: number;
  pd_multiplier: number;
}

export interface ScenarioAssumptions {
  enabled: boolean;
  base: ScenarioDefinition;
  upside: ScenarioDefinition;
  downside: ScenarioDefinition;
  staging_basis: StagingBasis;
}

// the "normal", non-scenario-weighted ECL: 100% weight on a single
// scenario with no PD adjustment, equivalent to the original single-PD
// calculation
export const SINGLE_SCENARIO: ScenarioAssumptions = {
  enabled: false,
  base: { weight: 1, pd_multiplier: 1.0 },
  upside: { weight: 0, pd_multiplier: 1.0 },
  downside: { weight: 0, pd_multiplier: 1.0 },
  staging_basis: "base_case",
};

export const DEFAULT_SCENARIO_ASSUMPTIONS: ScenarioAssumptions = {
  ...SINGLE_SCENARIO,
  enabled: false,
  base: { weight: 0.6, pd_multiplier: 1.0 },
  upside: { weight: 0.2, pd_multiplier: 0.8 },
  downside: { weight: 0.2, pd_multiplier: 1.5 },
};

export const SCENARIO_LABELS: Record<ScenarioName, string> = {
  base: "Base case",
  upside: "Upside",
  downside: "Downside",
};

export const STAGING_BASIS_LABELS: Record<StagingBasis, string> = {
  base_case: "Base case PD",
  scenario_weighted: "Scenario-weighted PD",
};
