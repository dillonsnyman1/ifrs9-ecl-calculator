# IFRS 9 staging and ECL calculation.
#
# Simplified version of the staging + ECL logic for demo purposes, not a
# production model. See the README for the methodology behind the
# thresholds and formulas below.

from app.models import (
    DiscountMethod,
    Loan,
    PortfolioResponse,
    PortfolioSummary,
    ProcessedLoan,
    Stage,
    StageSummary,
    StagingAssumptions,
)


def classify_stage(loan: Loan, staging: StagingAssumptions) -> Stage:
    """Work out which IFRS 9 stage a loan falls into."""
    if loan.days_past_due >= staging.stage_3_dpd_threshold:
        return Stage.stage_3

    sicr = (loan.pd_12m / loan.pd_origination) >= staging.sicr_pd_multiple
    if loan.days_past_due >= staging.stage_2_dpd_threshold or sicr:
        return Stage.stage_2

    return Stage.stage_1


def lifetime_pd(loan: Loan) -> float:
    """Roll the 12m PD forward over the remaining term to approximate lifetime PD."""
    years_remaining = loan.remaining_term_months / 12
    pd = 1 - (1 - loan.pd_12m) ** years_remaining
    return min(pd, 1.0)


def ecl_horizon_years(loan: Loan, stage: Stage) -> float:
    """How many years the ECL is calculated over: 1 year for stage 1, the
    remaining term for stage 2/3 (lifetime)."""
    if stage == Stage.stage_1:
        return 1.0
    return loan.remaining_term_months / 12


def discount_factor(loan: Loan, stage: Stage, method: DiscountMethod) -> float:
    """Discount the expected loss back to present value using the loan's EIR.

    We don't model a full cash shortfall schedule here, so this is a
    simplifying assumption about when the loss crystallises within the
    ECL horizon:
      - midpoint: half way through the horizon (our default)
      - end_of_horizon: at the end of the horizon (more conservative,
        gives a higher PV for the same undiscounted ECL)
    """
    horizon = ecl_horizon_years(loan, stage)
    years_to_loss = horizon / 2 if method == DiscountMethod.midpoint else horizon
    return 1 / (1 + loan.eir) ** years_to_loss


def calculate_ecl(loan: Loan, stage: Stage, pd_lt: float, method: DiscountMethod) -> tuple[float, float]:
    """Returns (discounted_ecl, undiscounted_ecl).

    ECL = PD x LGD x EAD. Stage 1 uses 12m PD, stage 2/3 use lifetime PD.
    The discounted figure applies the present value adjustment required
    by IFRS 9; the undiscounted figure is kept for comparison.
    """
    pd_used = loan.pd_12m if stage == Stage.stage_1 else pd_lt
    undiscounted = pd_used * loan.lgd * loan.exposure_at_default
    discounted = undiscounted * discount_factor(loan, stage, method)
    return discounted, undiscounted


def process_loan(loan: Loan, method: DiscountMethod, staging: StagingAssumptions) -> ProcessedLoan:
    stage = classify_stage(loan, staging)
    pd_lt = lifetime_pd(loan)
    ecl, ecl_undiscounted = calculate_ecl(loan, stage, pd_lt, method)
    return ProcessedLoan(
        **loan.model_dump(),
        stage=stage,
        pd_lifetime=pd_lt,
        ecl=ecl,
        ecl_undiscounted=ecl_undiscounted,
    )


def summarize_portfolio(loans: list[ProcessedLoan]) -> PortfolioSummary:
    total_exposure = sum(loan.exposure_at_default for loan in loans)
    total_ecl = sum(loan.ecl for loan in loans)
    total_ecl_undiscounted = sum(loan.ecl_undiscounted for loan in loans)

    by_stage: dict[Stage, StageSummary] = {}
    for stage in Stage:
        stage_loans = [loan for loan in loans if loan.stage == stage]
        by_stage[stage] = StageSummary(
            loan_count=len(stage_loans),
            exposure=sum(loan.exposure_at_default for loan in stage_loans),
            ecl=sum(loan.ecl for loan in stage_loans),
            ecl_undiscounted=sum(loan.ecl_undiscounted for loan in stage_loans),
        )

    coverage_ratio = total_ecl / total_exposure if total_exposure > 0 else 0.0

    return PortfolioSummary(
        loan_count=len(loans),
        total_exposure=total_exposure,
        total_ecl=total_ecl,
        total_ecl_undiscounted=total_ecl_undiscounted,
        coverage_ratio=coverage_ratio,
        by_stage=by_stage,
    )


def process_portfolio(
    loans: list[Loan],
    method: DiscountMethod = DiscountMethod.midpoint,
    staging: StagingAssumptions | None = None,
) -> PortfolioResponse:
    staging = staging or StagingAssumptions()
    processed = [process_loan(loan, method, staging) for loan in loans]
    summary = summarize_portfolio(processed)
    return PortfolioResponse(loans=processed, summary=summary)
