import pytest

from apothecaria.db.seed import seed_database
from apothecaria.domain.brewing import combine_ingredients


@pytest.fixture
def seeded_session(db_engine, db_session):
    with db_engine.connect() as conn:
        seed_database(conn)
    return db_session


def test_exact_match_returns_recipe(seeded_session):
    result = combine_ingredients(["moonpetal", "sage", "root"], seeded_session)
    assert result.matched_recipe_slug == "sleep_draught"
    assert result.matched_recipe_name == "Sleep Draught"
    assert result.matched_ailment_category == "sleep"
    assert result.quality_score == 1.0


def test_exact_match_unordered(seeded_session):
    result = combine_ingredients(["root", "moonpetal", "sage"], seeded_session)
    assert result.matched_recipe_slug == "sleep_draught"


def test_no_match_returns_none(seeded_session):
    result = combine_ingredients(["moonpetal", "feather"], seeded_session)
    assert result.matched_recipe_slug is None
    assert result.matched_ailment_category is None
    assert result.quality_score == 0.0


def test_unknown_ingredient_returns_failure(seeded_session):
    result = combine_ingredients(["dragon_scale"], seeded_session)
    assert result.matched_recipe_slug is None
    assert result.quality_score == 0.0


def test_empty_ingredients_returns_empty_brew(seeded_session):
    result = combine_ingredients([], seeded_session)
    assert result.matched_recipe_slug is None
    assert result.quality_score == 0.0
    assert "empty" in result.description.lower()


def test_extra_ingredient_is_not_a_match(seeded_session):
    result = combine_ingredients(["moonpetal", "sage", "root", "feather"], seeded_session)
    assert result.matched_recipe_slug is None


def test_subset_is_not_a_match(seeded_session):
    result = combine_ingredients(["moonpetal", "sage"], seeded_session)
    assert result.matched_recipe_slug is None


def test_fog_veil_exact_match(seeded_session):
    result = combine_ingredients(["moonpetal", "sage", "feather"], seeded_session)
    assert result.matched_recipe_slug == "fog_veil"
    assert result.matched_recipe_name == "Fog Veil"
    assert result.matched_ailment_category == "confusion"
    assert result.quality_score == 1.0


def test_iron_resolve_exact_match(seeded_session):
    result = combine_ingredients(["sage", "eye-of-newt", "root"], seeded_session)
    assert result.matched_recipe_slug == "iron_resolve"
    assert result.matched_recipe_name == "Iron Resolve"
    assert result.matched_ailment_category == "confusion"
    assert result.quality_score == 1.0
