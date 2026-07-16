import json

from sqlalchemy import select

from apothecaria.db.models import (
    BrewHistory,
    Ingredient,
    PlayerState,
    Recipe,
    RecipeIngredient,
)


def test_ingredient_round_trip(db_session):
    ing = Ingredient(slug="moonpetal", name="Moonpetal", lore="Glows on full moons.")
    db_session.add(ing)
    db_session.flush()
    fetched = db_session.get(Ingredient, ing.id)
    assert fetched is not None
    assert fetched.slug == "moonpetal"


def test_recipe_with_ingredients(db_session):
    moon = Ingredient(slug="moonpetal", name="Moonpetal")
    sage = Ingredient(slug="sage", name="Sage")
    db_session.add_all([moon, sage])
    db_session.flush()
    recipe = Recipe(slug="sleep_draught", name="Sleep Draught", ailment_category="sleep")
    recipe.ingredient_links = [
        RecipeIngredient(ingredient_id=moon.id),
        RecipeIngredient(ingredient_id=sage.id),
    ]
    db_session.add(recipe)
    db_session.flush()
    fetched = db_session.scalar(select(Recipe).where(Recipe.slug == "sleep_draught"))
    assert fetched is not None
    assert {link.ingredient.slug for link in fetched.ingredient_links} == {"moonpetal", "sage"}


def test_player_state_singleton(db_session):
    state = PlayerState(id=1, money=100, brews_count=0)
    db_session.add(state)
    db_session.flush()
    fetched = db_session.get(PlayerState, 1)
    assert fetched is not None
    assert fetched.money == 100


def test_brew_history_records_customer_snapshot(db_session):
    h = BrewHistory(
        ingredient_slugs=json.dumps(["moonpetal", "sage"]),
        matched_recipe_slug="sleep_draught",
        quality_score=1.0,
        customer_id="abc-123",
        customer_name="Weary Traveler",
        customer_ailment_category="sleep",
        expected_recipe_slug="sleep_draught",
        outcome="delighted",
        money_delta=10,
    )
    db_session.add(h)
    db_session.flush()
    assert h.id is not None
    assert h.customer_name == "Weary Traveler"
