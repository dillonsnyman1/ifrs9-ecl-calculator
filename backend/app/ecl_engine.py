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
    ScenarioAssumptions,
    ScenarioSummary,
    Stage,
    StageSummary,
    StagingAssumptions,
    StagingBasis,
)


def classify_stage(loan: Loan, staging: StagingAssumptions, pd_12m: float | None = None) -> Stage:
    """Work out which IFRS 9 stage a loan falls into.

    `pd_12m` defaults to the loan's own 12m PD, but a caller can pass an
    override (e.g. a scenario-weighted PD) to use for the SICR ratio test.
    """
    if loan.days_past_due >= staging.stage_3_dpd_threshold:
        return Stage.stage_3

    effective_pd_12m = loan.pd_12m if pd_12m is None else min(pd_12m, 1.0)
    sicr = (effective_pd_12m / loan.pd_origination) >= staging.sicr_pd_multiple
    if loan.days_past_due >= staging.stage_2_dpd_threshold or sicr:
        return Stage.stage_2

    return Stage.stage_1


def _lifetime_pd_from_pd(pd_12m: float, remaining_term_months: int) -> float:
    """Roll a 12m PD forward over the remaining term to approximate lifetime PD."""
    years_remaining = remaining_term_months / 12
    pd = 1 - (1 - pd_12m) ** years_remaining
    return min(pd, 1.0)


def lifetime_pd(loan: Loan) -> float:
    """Roll the loan's 12m PD forward over the remaining term to approximate lifetime PD."""
    return _lifetime_pd_from_pd(loan.pd_12m, loan.remaining_term_months)


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


def _ecl_for_pd(loan: Loan, stage: Stage, pd_12m: float, pd_lt: float, method: DiscountMethod) -> tuple[float, float]:
    """Returns (discounted_ecl, undiscounted_ecl) for the given 12m/lifetime PDs.

    ECL = PD x LGD x EAD. Stage 1 uses 12m PD, stage 2/3 use lifetime PD.
    The discounted figure applies the present value adjustment required
    by IFRS 9; the undiscounted figure is kept for comparison.
    """
    pd_used = pd_12m if stage == Stage.stage_1 else pd_lt
    undiscounted = pd_used * loan.lgd * loan.exposure_at_default
    discounted = undiscounted * discount_factor(loan, stage, method)
    return discounted, undiscounted


def calculate_ecl(loan: Loan, stage: Stage, pd_lt: float, method: DiscountMethod) -> tuple[float, float]:
    """Returns (discounted_ecl, undiscounted_ecl) using the loan's own 12m PD."""
    return _ecl_for_pd(loan, stage, loan.pd_12m, pd_lt, method)


def process_loan(
    loan: Loan,
    method: DiscountMethod,
    staging: StagingAssumptions,
    scenarios: ScenarioAssumptions,
) -> ProcessedLoan:
    # Apply each scenario's PD multiplier to get scenario-adjusted 12m and
    # lifetime PDs.
    scenario_pds = {
        name: (
            min(loan.pd_12m * definition.pd_multiplier, 1.0),
            _lifetime_pd_from_pd(min(loan.pd_12m * definition.pd_multiplier, 1.0), loan.remaining_term_months),
        )
        for name, definition in scenarios.items()
    }

    if scenarios.staging_basis == StagingBasis.scenario_weighted:
        weighted_pd_12m = sum(
            definition.weight * scenario_pds[name][0] for name, definition in scenarios.items()
        )
        stage = classify_stage(loan, staging, pd_12m=weighted_pd_12m)
    else:
        stage = classify_stage(loan, staging)

    ecl_scenarios = {}
    ecl_undiscounted_scenarios = {}
    ecl = 0.0
    ecl_undiscounted = 0.0
    for name, definition in scenarios.items():
        pd_12m_adj, pd_lt_adj = scenario_pds[name]
        ecl_s, ecl_u_s = _ecl_for_pd(loan, stage, pd_12m_adj, pd_lt_adj, method)
        ecl_scenarios[name] = ecl_s
        ecl_undiscounted_scenarios[name] = ecl_u_s
        ecl += definition.weight * ecl_s
        ecl_undiscounted += definition.weight * ecl_u_s

    return ProcessedLoan(
        **loan.model_dump(),
        stage=stage,
        pd_lifetime=lifetime_pd(loan),
        ecl=ecl,
        ecl_undiscounted=ecl_undiscounted,
        ecl_scenarios=ecl_scenarios,
        ecl_undiscounted_scenarios=ecl_undiscounted_scenarios,
    )


def summarize_portfolio(loans: list[ProcessedLoan], scenarios: ScenarioAssumptions) -> PortfolioSummary:
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

    by_scenario = {}
    for name, _ in scenarios.items():
        scenario_ecl = sum(loan.ecl_scenarios[name] for loan in loans)
        scenario_ecl_undiscounted = sum(loan.ecl_undiscounted_scenarios[name] for loan in loans)
        by_scenario[name] = ScenarioSummary(
            ecl=scenario_ecl,
            ecl_undiscounted=scenario_ecl_undiscounted,
            coverage_ratio=scenario_ecl / total_exposure if total_exposure > 0 else 0.0,
        )

    coverage_ratio = total_ecl / total_exposure if total_exposure > 0 else 0.0

    return PortfolioSummary(
        loan_count=len(loans),
        total_exposure=total_exposure,
        total_ecl=total_ecl,
        total_ecl_undiscounted=total_ecl_undiscounted,
        coverage_ratio=coverage_ratio,
        by_stage=by_stage,
        by_scenario=by_scenario,
        staging_basis=scenarios.staging_basis,
    )


def process_portfolio(
    loans: list[Loan],
    method: DiscountMethod = DiscountMethod.midpoint,
    staging: StagingAssumptions | None = None,
    scenarios: ScenarioAssumptions | None = None,
) -> PortfolioResponse:
    staging = staging or StagingAssumptions()
    scenarios = scenarios or ScenarioAssumptions()
    processed = [process_loan(loan, method, staging, scenarios) for loan in loans]
    summary = summarize_portfolio(processed, scenarios)
    return PortfolioResponse(loans=processed, summary=summary)
