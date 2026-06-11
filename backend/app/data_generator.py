# Generates a fake loan portfolio for the demo dataset.
#
# In practise ECL is calculated separately for each portfolio segment
# (mortgages, personal loans, credit cards, SME etc), since each one has
# its own PD/LGD models and parameter ranges. So this generator produces
# one portfolio at a time - the bundled sample is a retail personal loan
# book, but the same generator works for any segment if you tweak the
# ranges below.

import random

from app.models import Loan

PORTFOLIO_NAME = "personal_loan"

# rough parameter ranges for a retail personal loan book
EXPOSURE_RANGE = (2_000, 30_000)
LGD_RANGE = (0.40, 0.65)
PD_ORIGINATION_RANGE = (0.02, 0.08)
TERM_RANGE_MONTHS = (12, 60)
EIR_RANGE = (0.06, 0.12)


def _generate_loan(index: int, rng: random.Random) -> Loan:
    pd_origination = rng.uniform(*PD_ORIGINATION_RANGE)

    # most loans behave roughly as expected at origination, but give a
    # chunk of the book some deterioration so we get a mix of stages
    deterioration_roll = rng.random()
    if deterioration_roll < 0.10:
        # PD has jumped a lot - these end up stage 2 or 3
        pd_12m = min(pd_origination * rng.uniform(2.0, 6.0), 1.0)
        days_past_due = rng.choice([0, 30, 45, 60, 90, 120, 180])
    elif deterioration_roll < 0.25:
        # borderline cases, sitting around the stage 1/2 threshold
        pd_12m = min(pd_origination * rng.uniform(1.0, 2.0), 1.0)
        days_past_due = rng.choice([0, 0, 0, 15, 30])
    else:
        # performing fine
        pd_12m = pd_origination * rng.uniform(0.7, 1.1)
        days_past_due = 0

    return Loan(
        loan_id=f"L{index:05d}",
        product_type=PORTFOLIO_NAME,
        exposure_at_default=round(rng.uniform(*EXPOSURE_RANGE), 2),
        lgd=round(rng.uniform(*LGD_RANGE), 4),
        pd_12m=round(pd_12m, 4),
        pd_origination=round(pd_origination, 4),
        days_past_due=days_past_due,
        remaining_term_months=rng.randint(*TERM_RANGE_MONTHS),
        eir=round(rng.uniform(*EIR_RANGE), 4),
    )


def generate_portfolio(num_loans: int = 200, seed: int | None = 42) -> list[Loan]:
    rng = random.Random(seed)
    return [_generate_loan(i + 1, rng) for i in range(num_loans)]
