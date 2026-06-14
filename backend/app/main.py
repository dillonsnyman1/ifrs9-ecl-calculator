import os
from pathlib import Path

import pandas as pd
from fastapi import FastAPI, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import ValidationError

from app.ecl_engine import process_portfolio
from app.models import (
    DiscountMethod,
    Loan,
    PortfolioResponse,
    ScenarioAssumptions,
    ScenarioDefinition,
    StagingAssumptions,
    StagingBasis,
)

SAMPLE_DATA_PATH = Path(__file__).parent / "sample_data" / "sample_portfolio.csv"

app = FastAPI(title="IFRS 9 ECL Calculator")

# CORS_ORIGINS is a comma-separated list of allowed origins, e.g. the
# CloudFront domain in production. Defaults to the local Vite dev server.
CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "http://localhost:5173").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _loans_from_dataframe(df: pd.DataFrame) -> list[Loan]:
    try:
        return [Loan(**row) for row in df.to_dict(orient="records")]
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=f"Invalid loan data: {exc}") from exc


def _build_staging_assumptions(
    sicr_pd_multiple: float,
    stage_2_dpd_threshold: int,
    stage_3_dpd_threshold: int,
) -> StagingAssumptions:
    try:
        return StagingAssumptions(
            sicr_pd_multiple=sicr_pd_multiple,
            stage_2_dpd_threshold=stage_2_dpd_threshold,
            stage_3_dpd_threshold=stage_3_dpd_threshold,
        )
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=f"Invalid staging assumptions: {exc}") from exc


def _build_scenario_assumptions(
    scenario_base_weight: float,
    scenario_base_pd_multiplier: float,
    scenario_upside_weight: float,
    scenario_upside_pd_multiplier: float,
    scenario_downside_weight: float,
    scenario_downside_pd_multiplier: float,
    staging_basis: StagingBasis,
) -> ScenarioAssumptions:
    try:
        return ScenarioAssumptions(
            base=ScenarioDefinition(weight=scenario_base_weight, pd_multiplier=scenario_base_pd_multiplier),
            upside=ScenarioDefinition(weight=scenario_upside_weight, pd_multiplier=scenario_upside_pd_multiplier),
            downside=ScenarioDefinition(
                weight=scenario_downside_weight, pd_multiplier=scenario_downside_pd_multiplier
            ),
            staging_basis=staging_basis,
        )
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=f"Invalid scenario assumptions: {exc}") from exc


@app.get("/api/portfolio", response_model=PortfolioResponse)
def get_portfolio(
    discount_method: DiscountMethod = DiscountMethod.midpoint,
    sicr_pd_multiple: float = Query(default=2.0, gt=0),
    stage_2_dpd_threshold: int = Query(default=30, ge=0),
    stage_3_dpd_threshold: int = Query(default=90, ge=0),
    scenario_base_weight: float = Query(default=0.6, ge=0, le=1),
    scenario_base_pd_multiplier: float = Query(default=1.0, gt=0),
    scenario_upside_weight: float = Query(default=0.2, ge=0, le=1),
    scenario_upside_pd_multiplier: float = Query(default=0.8, gt=0),
    scenario_downside_weight: float = Query(default=0.2, ge=0, le=1),
    scenario_downside_pd_multiplier: float = Query(default=1.5, gt=0),
    staging_basis: StagingBasis = StagingBasis.base_case,
) -> PortfolioResponse:
    staging = _build_staging_assumptions(sicr_pd_multiple, stage_2_dpd_threshold, stage_3_dpd_threshold)
    scenarios = _build_scenario_assumptions(
        scenario_base_weight,
        scenario_base_pd_multiplier,
        scenario_upside_weight,
        scenario_upside_pd_multiplier,
        scenario_downside_weight,
        scenario_downside_pd_multiplier,
        staging_basis,
    )
    df = pd.read_csv(SAMPLE_DATA_PATH)
    loans = _loans_from_dataframe(df)
    return process_portfolio(loans, discount_method, staging, scenarios)


@app.post("/api/portfolio/upload", response_model=PortfolioResponse)
async def upload_portfolio(
    file: UploadFile,
    discount_method: DiscountMethod = DiscountMethod.midpoint,
    sicr_pd_multiple: float = Query(default=2.0, gt=0),
    stage_2_dpd_threshold: int = Query(default=30, ge=0),
    stage_3_dpd_threshold: int = Query(default=90, ge=0),
    scenario_base_weight: float = Query(default=0.6, ge=0, le=1),
    scenario_base_pd_multiplier: float = Query(default=1.0, gt=0),
    scenario_upside_weight: float = Query(default=0.2, ge=0, le=1),
    scenario_upside_pd_multiplier: float = Query(default=0.8, gt=0),
    scenario_downside_weight: float = Query(default=0.2, ge=0, le=1),
    scenario_downside_pd_multiplier: float = Query(default=1.5, gt=0),
    staging_basis: StagingBasis = StagingBasis.base_case,
) -> PortfolioResponse:
    staging = _build_staging_assumptions(sicr_pd_multiple, stage_2_dpd_threshold, stage_3_dpd_threshold)
    scenarios = _build_scenario_assumptions(
        scenario_base_weight,
        scenario_base_pd_multiplier,
        scenario_upside_weight,
        scenario_upside_pd_multiplier,
        scenario_downside_weight,
        scenario_downside_pd_multiplier,
        staging_basis,
    )

    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=422, detail="Please upload a CSV file.")

    try:
        df = pd.read_csv(file.file)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Could not read CSV file: {exc}") from exc

    required_columns = set(Loan.model_fields)
    missing = required_columns - set(df.columns)
    if missing:
        raise HTTPException(
            status_code=422,
            detail=f"CSV is missing required columns: {', '.join(sorted(missing))}",
        )

    loans = _loans_from_dataframe(df)
    return process_portfolio(loans, discount_method, staging, scenarios)


@app.get("/api/portfolio/sample-csv")
def download_sample_csv() -> FileResponse:
    return FileResponse(
        SAMPLE_DATA_PATH,
        media_type="text/csv",
        filename="sample_portfolio.csv",
    )


# AWS Lambda entrypoint (via API Gateway HTTP API proxy integration). Unused
# when running locally with uvicorn.
from mangum import Mangum  # noqa: E402

handler = Mangum(app)
