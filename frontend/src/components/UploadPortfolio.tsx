import { useRef, useState } from "react";

import { sampleCsvUrl, uploadPortfolio } from "../api/client";
import type { DiscountMethod, PortfolioResponse, StagingAssumptions } from "../types/portfolio";

interface Props {
  discountMethod: DiscountMethod;
  staging: StagingAssumptions;
  onUploaded: (data: PortfolioResponse, file: File) => void;
  onUseSample: () => void;
}

export function UploadPortfolio({ discountMethod, staging, onUploaded, onUseSample }: Props) {
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  async function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;

    setLoading(true);
    setError(null);
    try {
      const data = await uploadPortfolio(file, discountMethod, staging);
      onUploaded(data, file);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to upload portfolio.");
    } finally {
      setLoading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  }

  return (
    <div className="upload-portfolio">
      <label className="upload-button">
        {loading ? "Uploading..." : "Upload custom portfolio (CSV)"}
        <input ref={fileInputRef} type="file" accept=".csv" onChange={handleFileChange} disabled={loading} hidden />
      </label>
      <button type="button" className="link-button" onClick={onUseSample}>
        Use sample data
      </button>
      <a className="link-button" href={sampleCsvUrl()} download>
        Download CSV template
      </a>
      {error && <div className="upload-error">{error}</div>}
    </div>
  );
}
