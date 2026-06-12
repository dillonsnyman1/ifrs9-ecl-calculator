from pathlib import Path

import pandas as pd
from fastapi import FastAPI, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import ValidationError

from app.ecl_engine import process_portfolio
from app.models import DiscountMethod, Loan, PortfolioResponse, StagingAssumptions

SAMPLE_DATA_PATH = Path(__file__).parent / "sample_data" / "sample_portfolio.csv"

app = FastAPI(title="IFRS 9 ECL Calculator")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
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


@app.get("/api/portfolio", response_model=PortfolioResponse)
def get_portfolio(
    discount_method: DiscountMethod = DiscountMethod.midpoint,
    sicr_pd_multiple: float = Query(default=2.0, gt=0),
    stage_2_dpd_threshold: int = Query(default=30, ge=0),
    stage_3_dpd_threshold: int = Query(default=90, ge=0),
) -> PortfolioResponse:
    staging = _build_staging_assumptions(sicr_pd_multiple, stage_2_dpd_threshold, stage_3_dpd_threshold)
    df = pd.read_csv(SAMPLE_DATA_PATH)
    loans = _loans_from_dataframe(df)
    return process_portfolio(loans, discount_method, staging)


@app.post("/api/portfolio/upload", response_model=PortfolioResponse)
async def upload_portfolio(
    file: UploadFile,
    discount_method: DiscountMethod = DiscountMethod.midpoint,
    sicr_pd_multiple: float = Query(default=2.0, gt=0),
    stage_2_dpd_threshold: int = Query(default=30, ge=0),
    stage_3_dpd_threshold: int = Query(default=90, ge=0),
) -> PortfolioResponse:
    staging = _build_staging_assumptions(sicr_pd_multiple, stage_2_dpd_threshold, stage_3_dpd_threshold)

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
    return process_portfolio(loans, discount_method, staging)


@app.get("/api/portfolio/sample-csv")
def download_sample_csv() -> FileResponse:
    return FileResponse(
        SAMPLE_DATA_PATH,
        media_type="text/csv",
        filename="sample_portfolio.csv",
    )
