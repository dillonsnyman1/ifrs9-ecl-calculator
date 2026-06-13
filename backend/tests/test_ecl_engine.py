import pytest

from app.ecl_engine import calculate_ecl, classify_stage, discount_factor, lifetime_pd, process_portfolio
from app.models import (
    DiscountMethod,
    Loan,
    ScenarioAssumptions,
    ScenarioDefinition,
    ScenarioName,
    Stage,
    StagingAssumptions,
    StagingBasis,
)

DEFAULT_STAGING = StagingAssumptions()
DEFAULT_SCENARIOS = ScenarioAssumptions()


def make_loan(**overrides) -> Loan:
    defaults = dict(
        loan_id="L00001",
        product_type="personal_loan",
        exposure_at_default=10_000.0,
        lgd=0.5,
        pd_12m=0.02,
        pd_origination=0.02,
        days_past_due=0,
        remaining_term_months=24,
        eir=0.10,
    )
    defaults.update(overrides)
    return Loan(**defaults)


def test_classify_stage_1_when_performing():
    loan = make_loan(pd_12m=0.02, pd_origination=0.02, days_past_due=0)
    assert classify_stage(loan, DEFAULT_STAGING) == Stage.stage_1


def test_classify_stage_2_when_pd_doubles():
    loan = make_loan(pd_12m=0.05, pd_origination=0.02, days_past_due=0)
    assert classify_stage(loan, DEFAULT_STAGING) == Stage.stage_2


def test_classify_stage_2_when_30_dpd():
    loan = make_loan(pd_12m=0.02, pd_origination=0.02, days_past_due=30)
    assert classify_stage(loan, DEFAULT_STAGING) == Stage.stage_2


def test_classify_stage_3_when_90_dpd():
    loan = make_loan(pd_12m=0.02, pd_origination=0.02, days_past_due=90)
    assert classify_stage(loan, DEFAULT_STAGING) == Stage.stage_3


def test_classify_stage_uses_custom_sicr_multiple():
    loan = make_loan(pd_12m=0.05, pd_origination=0.02, days_past_due=0)
    # pd ratio is 2.5x, default 2.0x multiple would flag this as stage 2
    assert classify_stage(loan, DEFAULT_STAGING) == Stage.stage_2

    staging = StagingAssumptions(sicr_pd_multiple=3.0)
    assert classify_stage(loan, staging) == Stage.stage_1


def test_classify_stage_uses_custom_dpd_thresholds():
    loan = make_loan(pd_12m=0.02, pd_origination=0.02, days_past_due=45)
    # default thresholds (30/90) would put this in stage 2
    assert classify_stage(loan, DEFAULT_STAGING) == Stage.stage_2

    staging = StagingAssumptions(stage_2_dpd_threshold=60, stage_3_dpd_threshold=120)
    assert classify_stage(loan, staging) == Stage.stage_1


def test_staging_assumptions_rejects_stage_3_below_stage_2():
    with pytest.raises(ValueError):
        StagingAssumptions(stage_2_dpd_threshold=90, stage_3_dpd_threshold=30)


def test_lifetime_pd_matches_12m_pd_at_one_year_term():
    loan = make_loan(pd_12m=0.05, remaining_term_months=12)
    assert lifetime_pd(loan) == pytest.approx(0.05)


def test_lifetime_pd_compounds_over_longer_term():
    loan = make_loan(pd_12m=0.05, remaining_term_months=24)
    expected = 1 - (1 - 0.05) ** 2
    assert lifetime_pd(loan) == pytest.approx(expected)


def test_stage_1_ecl_uses_12m_pd_discounted_six_months():
    loan = make_loan(pd_12m=0.02, pd_origination=0.02, days_past_due=0,
                      lgd=0.5, exposure_at_default=10_000.0, eir=0.10)
    stage = classify_stage(loan, DEFAULT_STAGING)
    pd_lt = lifetime_pd(loan)
    ecl, ecl_undiscounted = calculate_ecl(loan, stage, pd_lt, DiscountMethod.midpoint)
    assert stage == Stage.stage_1
    assert ecl_undiscounted == pytest.approx(0.02 * 0.5 * 10_000.0)
    expected = ecl_undiscounted / (1 + 0.10) ** 0.5
    assert ecl == pytest.approx(expected)
    assert ecl < ecl_undiscounted


def test_stage_2_ecl_uses_lifetime_pd_discounted_to_term_midpoint():
    loan = make_loan(pd_12m=0.05, pd_origination=0.02, days_past_due=0,
                      lgd=0.5, exposure_at_default=10_000.0, remaining_term_months=24, eir=0.10)
    stage = classify_stage(loan, DEFAULT_STAGING)
    pd_lt = lifetime_pd(loan)
    ecl, ecl_undiscounted = calculate_ecl(loan, stage, pd_lt, DiscountMethod.midpoint)
    assert stage == Stage.stage_2
    assert ecl_undiscounted == pytest.approx(pd_lt * 0.5 * 10_000.0)
    expected = ecl_undiscounted / (1 + 0.10) ** 1.0  # 2 year term, midpoint = 1 year
    assert ecl == pytest.approx(expected)
    assert ecl < ecl_undiscounted


def test_end_of_horizon_discounts_more_than_midpoint():
    loan = make_loan(pd_12m=0.05, pd_origination=0.02, days_past_due=0,
                      lgd=0.5, exposure_at_default=10_000.0, remaining_term_months=24, eir=0.10)
    stage = classify_stage(loan, DEFAULT_STAGING)
    pd_lt = lifetime_pd(loan)
    ecl_midpoint, _ = calculate_ecl(loan, stage, pd_lt, DiscountMethod.midpoint)
    ecl_end, ecl_undiscounted = calculate_ecl(loan, stage, pd_lt, DiscountMethod.end_of_horizon)
    assert ecl_end == pytest.approx(ecl_undiscounted / (1 + 0.10) ** 2.0)  # full 2 year term
    assert ecl_end < ecl_midpoint


def test_discount_factor_uses_midpoint_of_remaining_term_for_lifetime_ecl():
    loan = make_loan(remaining_term_months=36, eir=0.08)
    factor = discount_factor(loan, Stage.stage_2, DiscountMethod.midpoint)
    assert factor == pytest.approx(1 / (1.08 ** 1.5))


def test_process_portfolio_summary_aggregates_correctly():
    loans = [
        make_loan(loan_id="L1", exposure_at_default=10_000.0, lgd=0.5,
                  pd_12m=0.02, pd_origination=0.02, days_past_due=0),
        make_loan(loan_id="L2", exposure_at_default=20_000.0, lgd=0.5,
                  pd_12m=0.10, pd_origination=0.02, days_past_due=0),
        make_loan(loan_id="L3", exposure_at_default=5_000.0, lgd=1.0,
                  pd_12m=0.5, pd_origination=0.02, days_past_due=120),
    ]

    response = process_portfolio(loans)

    assert response.summary.loan_count == 3
    assert response.summary.total_exposure == pytest.approx(35_000.0)
    assert response.summary.total_ecl == pytest.approx(sum(loan.ecl for loan in response.loans))
    assert response.summary.total_ecl_undiscounted == pytest.approx(
        sum(loan.ecl_undiscounted for loan in response.loans)
    )
    assert response.summary.total_ecl < response.summary.total_ecl_undiscounted
    assert response.summary.coverage_ratio == pytest.approx(
        response.summary.total_ecl / response.summary.total_exposure
    )

    assert response.loans[0].stage == Stage.stage_1
    assert response.loans[1].stage == Stage.stage_2
    assert response.loans[2].stage == Stage.stage_3

    assert response.summary.by_stage[Stage.stage_1].loan_count == 1
    assert response.summary.by_stage[Stage.stage_2].loan_count == 1
    assert response.summary.by_stage[Stage.stage_3].loan_count == 1


def test_scenario_assumptions_rejects_weights_not_summing_to_one():
    with pytest.raises(ValueError):
        ScenarioAssumptions(
            base=ScenarioDefinition(weight=0.5, pd_multiplier=1.0),
            upside=ScenarioDefinition(weight=0.5, pd_multiplier=0.8),
            downside=ScenarioDefinition(weight=0.5, pd_multiplier=1.5),
        )


def test_classify_stage_uses_pd_override_for_sicr_test():
    loan = make_loan(pd_12m=0.02, pd_origination=0.02, days_past_due=0)
    assert classify_stage(loan, DEFAULT_STAGING) == Stage.stage_1
    # an override pd_12m that is 2.5x origination should push it to stage 2
    assert classify_stage(loan, DEFAULT_STAGING, pd_12m=0.05) == Stage.stage_2


def test_process_loan_ecl_is_probability_weighted_average_of_scenarios():
    loan = make_loan(pd_12m=0.02, pd_origination=0.02, days_past_due=0,
                      lgd=0.5, exposure_at_default=10_000.0, eir=0.10)

    response = process_portfolio([loan], DiscountMethod.midpoint, DEFAULT_STAGING, DEFAULT_SCENARIOS)
    processed = response.loans[0]

    assert processed.stage == Stage.stage_1

    expected_ecl = 0.0
    expected_ecl_undiscounted = 0.0
    for name, definition in DEFAULT_SCENARIOS.items():
        pd_12m_adj = loan.pd_12m * definition.pd_multiplier
        ecl_s, ecl_u_s = calculate_ecl(
            loan.model_copy(update={"pd_12m": pd_12m_adj}), processed.stage, lifetime_pd(loan), DiscountMethod.midpoint
        )
        assert processed.ecl_scenarios[name] == pytest.approx(ecl_s)
        assert processed.ecl_undiscounted_scenarios[name] == pytest.approx(ecl_u_s)
        expected_ecl += definition.weight * ecl_s
        expected_ecl_undiscounted += definition.weight * ecl_u_s

    assert processed.ecl == pytest.approx(expected_ecl)
    assert processed.ecl_undiscounted == pytest.approx(expected_ecl_undiscounted)


def test_scenario_weighted_staging_can_flip_stage_vs_base_case():
    # pd_12m / pd_origination = 1.9, below the 2.0 SICR multiple, so base-case
    # staging keeps this at stage 1.
    loan = make_loan(pd_12m=0.038, pd_origination=0.02, days_past_due=0)

    base_case_scenarios = ScenarioAssumptions(staging_basis=StagingBasis.base_case)
    scenario_weighted = ScenarioAssumptions(staging_basis=StagingBasis.scenario_weighted)

    base_response = process_portfolio([loan], DiscountMethod.midpoint, DEFAULT_STAGING, base_case_scenarios)
    assert base_response.loans[0].stage == Stage.stage_1

    # the default scenario weights/multipliers push the weighted pd_12m to
    # 1.9 * 1.06 = 2.014x origination, crossing the 2.0 SICR multiple.
    weighted_response = process_portfolio([loan], DiscountMethod.midpoint, DEFAULT_STAGING, scenario_weighted)
    assert weighted_response.loans[0].stage == Stage.stage_2


def test_process_portfolio_by_scenario_summary():
    loans = [
        make_loan(loan_id="L1", exposure_at_default=10_000.0, lgd=0.5,
                  pd_12m=0.02, pd_origination=0.02, days_past_due=0),
        make_loan(loan_id="L2", exposure_at_default=20_000.0, lgd=0.5,
                  pd_12m=0.10, pd_origination=0.02, days_past_due=0),
    ]

    response = process_portfolio(loans, DiscountMethod.midpoint, DEFAULT_STAGING, DEFAULT_SCENARIOS)

    assert response.summary.staging_basis == StagingBasis.base_case

    for name in (ScenarioName.base, ScenarioName.upside, ScenarioName.downside):
        expected_ecl = sum(loan.ecl_scenarios[name] for loan in response.loans)
        expected_ecl_undiscounted = sum(loan.ecl_undiscounted_scenarios[name] for loan in response.loans)
        assert response.summary.by_scenario[name].ecl == pytest.approx(expected_ecl)
        assert response.summary.by_scenario[name].ecl_undiscounted == pytest.approx(expected_ecl_undiscounted)
        assert response.summary.by_scenario[name].coverage_ratio == pytest.approx(
            expected_ecl / response.summary.total_exposure
        )

    # downside scenario (higher PD multiplier) should produce more ECL than upside
    assert response.summary.by_scenario[ScenarioName.downside].ecl > response.summary.by_scenario[ScenarioName.upside].ecl
