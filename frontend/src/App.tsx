import { useEffect, useState } from "react";

import "./App.css";
import { fetchSamplePortfolio, uploadPortfolio } from "./api/client";
import { EclByStageChart } from "./components/EclByStageChart";
import { LoanTable } from "./components/LoanTable";
import { StageBreakdownChart } from "./components/StageBreakdownChart";
import { SummaryCards } from "./components/SummaryCards";
import { UploadPortfolio } from "./components/UploadPortfolio";
import { DISCOUNT_METHOD_LABELS, type DiscountMethod, type PortfolioResponse } from "./types/portfolio";

function App() {
  const [portfolio, setPortfolio] = useState<PortfolioResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [discountMethod, setDiscountMethod] = useState<DiscountMethod>("midpoint");
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);

  function loadSample(method: DiscountMethod) {
    setLoading(true);
    setError(null);
    fetchSamplePortfolio(method)
      .then(setPortfolio)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load portfolio."))
      .finally(() => setLoading(false));
  }

  function reloadUploadedFile(file: File, method: DiscountMethod) {
    setLoading(true);
    setError(null);
    uploadPortfolio(file, method)
      .then(setPortfolio)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load portfolio."))
      .finally(() => setLoading(false));
  }

  function handleUseSample() {
    setUploadedFile(null);
    loadSample(discountMethod);
  }

  function handleUploaded(data: PortfolioResponse, file: File) {
    setUploadedFile(file);
    setPortfolio(data);
  }

  function handleDiscountMethodChange(method: DiscountMethod) {
    setDiscountMethod(method);
    if (uploadedFile) {
      reloadUploadedFile(uploadedFile, method);
    } else {
      loadSample(method);
    }
  }

  useEffect(() => {
    // loading and error are already at their initial values on mount, so just
    // kick off the fetch directly rather than going through loadSample
    fetchSamplePortfolio(discountMethod)
      .then(setPortfolio)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load portfolio."))
      .finally(() => setLoading(false));
    // only run once on mount, discount method changes are handled separately
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
        <UploadPortfolio discountMethod={discountMethod} onUploaded={handleUploaded} onUseSample={handleUseSample} />

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
