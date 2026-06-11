from enum import Enum

from pydantic import BaseModel, Field


class Stage(str, Enum):
    stage_1 = "stage_1"
    stage_2 = "stage_2"
    stage_3 = "stage_3"


class DiscountMethod(str, Enum):
    """When the expected loss is assumed to crystallise within the ECL horizon."""

    midpoint = "midpoint"
    end_of_horizon = "end_of_horizon"


class Loan(BaseModel):
    """Loan-level inputs that go into the ECL engine."""

    loan_id: str
    product_type: str = Field(min_length=1, description="portfolio segment, e.g. mortgages, sme term loans")
    exposure_at_default: float = Field(gt=0)
    lgd: float = Field(ge=0, le=1)
    pd_12m: float = Field(ge=0, le=1)
    pd_origination: float = Field(gt=0, le=1)
    days_past_due: int = Field(ge=0)
    remaining_term_months: int = Field(ge=0)
    eir: float = Field(gt=0, description="effective interest rate, used to discount ECL to present value")


class ProcessedLoan(Loan):
    """Loan with staging and ECL already worked out."""

    stage: Stage
    pd_lifetime: float
    ecl: float
    ecl_undiscounted: float


class StageSummary(BaseModel):
    loan_count: int
    exposure: float
    ecl: float
    ecl_undiscounted: float


class PortfolioSummary(BaseModel):
    loan_count: int
    total_exposure: float
    total_ecl: float
    total_ecl_undiscounted: float
    coverage_ratio: float
    by_stage: dict[Stage, StageSummary]


class PortfolioResponse(BaseModel):
    loans: list[ProcessedLoan]
    summary: PortfolioSummary
