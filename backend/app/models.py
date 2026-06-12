from enum import Enum

from pydantic import BaseModel, Field, model_validator


class Stage(str, Enum):
    stage_1 = "stage_1"
    stage_2 = "stage_2"
    stage_3 = "stage_3"


class DiscountMethod(str, Enum):
    """When the expected loss is assumed to crystallise within the ECL horizon."""

    midpoint = "midpoint"
    end_of_horizon = "end_of_horizon"


class StagingAssumptions(BaseModel):
    """The backstops used to decide when a loan moves to stage 2 or 3.

    These are configurable so users can see how sensitive the staging
    (and therefore the ECL) is to the thresholds chosen.
    """

    sicr_pd_multiple: float = Field(
        default=2.0,
        gt=0,
        description="loan moves to stage 2 if pd_12m / pd_origination is at least this multiple",
    )
    stage_2_dpd_threshold: int = Field(default=30, ge=0, description="days past due backstop for stage 2")
    stage_3_dpd_threshold: int = Field(default=90, ge=0, description="days past due backstop for stage 3 (default)")

    @model_validator(mode="after")
    def check_thresholds_ordered(self) -> "StagingAssumptions":
        if self.stage_3_dpd_threshold < self.stage_2_dpd_threshold:
            raise ValueError("stage_3_dpd_threshold must be greater than or equal to stage_2_dpd_threshold")
        return self


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
