from datetime import datetime

import pytest
from sqlalchemy import select

from apothecaria.db.models import BrewHistory, PlayerState
from apothecaria.db.seed import STARTING_MONEY, seed_database
from apothecaria.domain.economy import apply_outcome, determine_outcome
from apothecaria.domain.models import BrewResult, CustomerInstance, Outcome


def _customer(category: str = "sleep", expected: str = "sleep_draught") -> CustomerInstance:
    return CustomerInstance(
        id="c-1",
        template_slug="weary_traveler",
        name="Weary Traveler",
        persona="impatient_farmer",
        ailment_narrative="...",
        ailment_category=category,
        expected_recipe_slug=expected,
        arrived_at=datetime.utcnow(),
    )


def _brew(
    recipe_slug: str | None = None,
    recipe_name: str | None = None,
    ailment_category: str | None = None,
) -> BrewResult:
    return BrewResult(
        matched_recipe_slug=recipe_slug,
        matched_recipe_name=recipe_name,
        matched_ailment_category=ailment_category,
        quality_score=1.0 if recipe_slug else 0.0,
        ingredient_slugs=["x"],
        description="...",
    )


def test_correct_potion_is_delighted():
    o, d, _ = determine_outcome(_brew("sleep_draught", "Sleep Draught", "sleep"), _customer())
    assert o == Outcome.DELIGHTED
    assert d == 10


def test_right_category_wrong_recipe_is_neutral():
    """Brewed a known potion that addresses the customer's category, but not the specific one expected."""
    o, d, _ = determine_outcome(_brew("dream_tea", "Dream Tea", "sleep"), _customer())
    assert o == Outcome.NEUTRAL
    assert d == 1


def test_wrong_category_is_disappointed():
    o, d, _ = determine_outcome(_brew("energy_elixir", "Energy Elixir", "fatigue"), _customer())
    assert o == Outcome.DISAPPOINTED
    assert d == -5


def test_unknown_brew_is_confused():
    o, d, _ = determine_outcome(_brew(None), _customer())
    assert o == Outcome.CONFUSED
    assert d == -2


@pytest.fixture
def seeded_session(db_engine, db_session):
    with db_engine.connect() as conn:
        seed_database(conn)
    return db_session


def test_apply_outcome_writes_brew_history(seeded_session):
    customer = _customer()
    apply_outcome(_brew("sleep_draught", "Sleep Draught", "sleep"), customer, seeded_session)
    rows = list(seeded_session.scalars(select(BrewHistory)))
    assert len(rows) == 1
    row = rows[0]
    assert row.outcome == "delighted"
    assert row.customer_id == "c-1"
    assert row.customer_name == "Weary Traveler"
    assert row.matched_recipe_slug == "sleep_draught"
    assert row.money_delta == 10


def test_apply_outcome_updates_player_state(seeded_session):
    customer = _customer()
    result = apply_outcome(
        _brew("sleep_draught", "Sleep Draught", "sleep"), customer, seeded_session
    )
    state = seeded_session.get(PlayerState, 1)
    assert state.money == STARTING_MONEY + 10
    assert state.brews_count == 1
    assert result.new_money == STARTING_MONEY + 10
