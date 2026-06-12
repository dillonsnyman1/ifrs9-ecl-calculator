import type { DiscountMethod, PortfolioResponse, StagingAssumptions } from "../types/portfolio";

const API_BASE = "http://localhost:8000";

function stagingParams(staging: StagingAssumptions): string {
  return new URLSearchParams({
    sicr_pd_multiple: String(staging.sicr_pd_multiple),
    stage_2_dpd_threshold: String(staging.stage_2_dpd_threshold),
    stage_3_dpd_threshold: String(staging.stage_3_dpd_threshold),
  }).toString();
}

export async function fetchSamplePortfolio(
  discountMethod: DiscountMethod,
  staging: StagingAssumptions,
): Promise<PortfolioResponse> {
  const res = await fetch(`${API_BASE}/api/portfolio?discount_method=${discountMethod}&${stagingParams(staging)}`);
  if (!res.ok) {
    throw new Error(`Failed to load portfolio (${res.status})`);
  }
  return res.json();
}

export async function uploadPortfolio(
  file: File,
  discountMethod: DiscountMethod,
  staging: StagingAssumptions,
): Promise<PortfolioResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch(
    `${API_BASE}/api/portfolio/upload?discount_method=${discountMethod}&${stagingParams(staging)}`,
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
