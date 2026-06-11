import type { DiscountMethod, PortfolioResponse } from "../types/portfolio";

const API_BASE = "http://localhost:8000";

export async function fetchSamplePortfolio(discountMethod: DiscountMethod): Promise<PortfolioResponse> {
  const res = await fetch(`${API_BASE}/api/portfolio?discount_method=${discountMethod}`);
  if (!res.ok) {
    throw new Error(`Failed to load portfolio (${res.status})`);
  }
  return res.json();
}

export async function uploadPortfolio(file: File, discountMethod: DiscountMethod): Promise<PortfolioResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch(`${API_BASE}/api/portfolio/upload?discount_method=${discountMethod}`, {
    method: "POST",
    body: formData,
  });

  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new Error(body?.detail ?? `Failed to upload portfolio (${res.status})`);
  }

  return res.json();
}

export function sampleCsvUrl(): string {
  return `${API_BASE}/api/portfolio/sample-csv`;
}
