import { useEffect, useState } from "react";

import "./App.css";
import { fetchSamplePortfolio, uploadPortfolio } from "./api/client";
import { EclByStageChart } from "./components/EclByStageChart";
import { LoanTable } from "./components/LoanTable";
import { StageBreakdownChart } from "./components/StageBreakdownChart";
import { StagingControls } from "./components/StagingControls";
import { SummaryCards } from "./components/SummaryCards";
import { UploadPortfolio } from "./components/UploadPortfolio";
import {
  DEFAULT_STAGING_ASSUMPTIONS,
  DISCOUNT_METHOD_LABELS,
  type DiscountMethod,
  type PortfolioResponse,
  type StagingAssumptions,
} from "./types/portfolio";

function App() {
  const [portfolio, setPortfolio] = useState<PortfolioResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [discountMethod, setDiscountMethod] = useState<DiscountMethod>("midpoint");
  const [staging, setStaging] = useState<StagingAssumptions>(DEFAULT_STAGING_ASSUMPTIONS);
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);

  function loadSample(method: DiscountMethod, staging: StagingAssumptions) {
    setLoading(true);
    setError(null);
    fetchSamplePortfolio(method, staging)
      .then(setPortfolio)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load portfolio."))
      .finally(() => setLoading(false));
  }

  function reloadUploadedFile(file: File, method: DiscountMethod, staging: StagingAssumptions) {
    setLoading(true);
    setError(null);
    uploadPortfolio(file, method, staging)
      .then(setPortfolio)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load portfolio."))
      .finally(() => setLoading(false));
  }

  function handleUseSample() {
    setUploadedFile(null);
    loadSample(discountMethod, staging);
  }

  function handleUploaded(data: PortfolioResponse, file: File) {
    setUploadedFile(file);
    setPortfolio(data);
  }

  function handleDiscountMethodChange(method: DiscountMethod) {
    setDiscountMethod(method);
    if (uploadedFile) {
      reloadUploadedFile(uploadedFile, method, staging);
    } else {
      loadSample(method, staging);
    }
  }

  function handleStagingChange(nextStaging: StagingAssumptions) {
    setStaging(nextStaging);
    if (uploadedFile) {
      reloadUploadedFile(uploadedFile, discountMethod, nextStaging);
    } else {
      loadSample(discountMethod, nextStaging);
    }
  }

  useEffect(() => {
    // loading and error are already at their initial values on mount, so just
    // kick off the fetch directly rather than going through loadSample
    fetchSamplePortfolio(discountMethod, staging)
      .then(setPortfolio)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load portfolio."))
      .finally(() => setLoading(false));
    // only run once on mount, discount method and staging changes are handled separately
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <>
      <header className="app-header">
        <h1>IFRS 9 ECL Calculator</h1>
        <p>
          A simplified, illustrative IFRS 9 expected credit loss (ECL) engine. Loans are classified
          into Stage 1, 2 or 3 based on days past due and changes in PD since origination, with
          12-month or lifetime ECL calculated as PD × LGD × EAD accordingly.
        </p>
      </header>

      <div className="toolbar">
        <UploadPortfolio
          discountMethod={discountMethod}
          staging={staging}
          onUploaded={handleUploaded}
          onUseSample={handleUseSample}
        />

        <div className="discount-method-control">
          <label htmlFor="discount-method">Discount timing assumption</label>
          <select
            id="discount-method"
            value={discountMethod}
            onChange={(e) => handleDiscountMethodChange(e.target.value as DiscountMethod)}
          >
            {Object.entries(DISCOUNT_METHOD_LABELS).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>
          <span className="discount-method-hint">
            Assumes the expected loss crystallises at this point within the ECL horizon.
          </span>
        </div>
      </div>

      <div className="toolbar">
        <StagingControls staging={staging} onApply={handleStagingChange} />
      </div>

      {loading && <div className="status-message">Loading portfolio...</div>}
      {error && <div className="status-message error">{error}</div>}

      {portfolio && !loading && (
        <>
          <SummaryCards summary={portfolio.summary} />
          <div className="charts-row">
            <StageBreakdownChart summary={portfolio.summary} />
            <EclByStageChart summary={portfolio.summary} />
          </div>
          <LoanTable loans={portfolio.loans} />
        </>
      )}
    </>
  );
}

export default App;
