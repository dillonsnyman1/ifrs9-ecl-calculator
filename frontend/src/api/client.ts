import type { DiscountMethod, PortfolioResponse, ScenarioAssumptions, StagingAssumptions } from "../types/portfolio";
import { SINGLE_SCENARIO } from "../types/portfolio";

// In production this is set at build time to the deployed API Gateway URL
// (see .github/workflows/deploy.yml); locally it falls back to the FastAPI
// dev server.
const API_BASE: string = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

function stagingParams(staging: StagingAssumptions): string {
  return new URLSearchParams({
    sicr_pd_multiple: String(staging.sicr_pd_multiple),
    stage_2_dpd_threshold: String(staging.stage_2_dpd_threshold),
    stage_3_dpd_threshold: String(staging.stage_3_dpd_threshold),
  }).toString();
}

function scenarioParams(scenarios: ScenarioAssumptions): string {
  // when scenario weighting is switched off, fall back to a single
  // unweighted scenario so ECL matches the original single-PD calculation
  const effective = scenarios.enabled ? scenarios : SINGLE_SCENARIO;
  return new URLSearchParams({
    scenario_base_weight: String(effective.base.weight),
    scenario_base_pd_multiplier: String(effective.base.pd_multiplier),
    scenario_upside_weight: String(effective.upside.weight),
    scenario_upside_pd_multiplier: String(effective.upside.pd_multiplier),
    scenario_downside_weight: String(effective.downside.weight),
    scenario_downside_pd_multiplier: String(effective.downside.pd_multiplier),
    staging_basis: effective.staging_basis,
  }).toString();
}

export async function fetchSamplePortfolio(
  discountMethod: DiscountMethod,
  staging: StagingAssumptions,
  scenarios: ScenarioAssumptions,
): Promise<PortfolioResponse> {
  const res = await fetch(
    `${API_BASE}/api/portfolio?discount_method=${discountMethod}&${stagingParams(staging)}&${scenarioParams(scenarios)}`,
  );
  if (!res.ok) {
    throw new Error(`Failed to load portfolio (${res.status})`);
  }
  return res.json();
}

export async function uploadPortfolio(
  file: File,
  discountMethod: DiscountMethod,
  staging: StagingAssumptions,
  scenarios: ScenarioAssumptions,
): Promise<PortfolioResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch(
    `${API_BASE}/api/portfolio/upload?discount_method=${discountMethod}&${stagingParams(staging)}&${scenarioParams(scenarios)}`,
    {
      method: "POST",
      body: formData,
    },
  );

  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new Error(body?.detail ?? `Failed to upload portfolio (${res.status})`);
  }

  return res.json();
}

export function sampleCsvUrl(): string {
  return `${API_BASE}/api/portfolio/sample-csv`;
}
