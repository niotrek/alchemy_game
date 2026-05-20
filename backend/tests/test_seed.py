import json

import pytest
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from apothecaria.db.models import Ingredient, PlayerInventory, PlayerState, Recipe, StoreItem
from apothecaria.db.seed import _seed_ingredients, seed_database


def test_seed_loads_ingredients(db_engine):
    with db_engine.connect() as conn:
        seed_database(conn)
    with Session(db_engine) as session:
        slugs = {i.slug for i in session.scalars(select(Ingredient)).all()}
    assert {"moonpetal", "mushroom", "root", "feather", "eye-of-newt", "sage"} <= slugs


def test_seed_loads_recipes_with_ingredients(db_engine):
    with db_engine.connect() as conn:
        seed_database(conn)
    with Session(db_engine) as session:
        sleep = session.scalar(select(Recipe).where(Recipe.slug == "sleep_draught"))
        assert sleep is not None
        assert {link.ingredient.slug for link in sleep.ingredient_links} == {
            "moonpetal",
            "sage",
            "root",
        }


def test_seed_creates_player_state(db_engine):
    with db_engine.connect() as conn:
        seed_database(conn)
    with Session(db_engine) as session:
        state = session.get(PlayerState, 1)
        assert state is not None
        assert state.money == 100


def test_seed_is_idempotent_no_duplicates(db_engine):
    with db_engine.connect() as conn:
        seed_database(conn)
        seed_database(conn)
    with Session(db_engine) as session:
        assert len(session.scalars(select(Ingredient)).all()) == 6
        assert len(session.scalars(select(Recipe)).all()) == 5


def test_seed_upserts_existing_rows(db_engine):
    """If an ingredient row exists with stale data, re-seeding refreshes it from JSON."""
    with db_engine.connect() as conn:
        seed_database(conn)
    with Session(db_engine) as session:
        moon = session.scalar(select(Ingredient).where(Ingredient.slug == "moonpetal"))
        assert moon is not None
        moon.lore = "STALE LORE"
        session.commit()
    with db_engine.connect() as conn:
        seed_database(conn)
    with Session(db_engine) as session:
        moon = session.scalar(select(Ingredient).where(Ingredient.slug == "moonpetal"))
    assert moon is not None
    assert moon.lore != "STALE LORE"
    assert "moon" in moon.lore.lower()


def test_seed_validation_rejects_bad_data(tmp_path, monkeypatch, db_engine):
    """A bad ingredients.json (empty slug) raises pydantic ValidationError."""
    bad = tmp_path / "ingredients.json"
    bad.write_text(json.dumps([{"slug": "", "name": "Anonymous"}]))
    import apothecaria.db.seed as seed_mod

    monkeypatch.setattr(seed_mod, "CONTENT_DIR", tmp_path)
    with Session(db_engine) as session, pytest.raises(ValidationError):
        _seed_ingredients(session)


def test_seed_creates_player_inventory(db_engine):
    with db_engine.connect() as conn:
        seed_database(conn)
    with Session(db_engine) as session:
        rows = session.scalars(select(PlayerInventory)).all()
        assert len(rows) == 6
        for row in rows:
            assert row.quantity == 20


def test_seed_creates_store_items(db_engine):
    with db_engine.connect() as conn:
        seed_database(conn)
    with Session(db_engine) as session:
        items = session.scalars(select(StoreItem)).all()
        assert len(items) == 6
        slugs_prices = {item.ingredient.slug: item.price for item in items}
        assert slugs_prices["moonpetal"] == 5
        assert slugs_prices["eye-of-newt"] == 8
        for item in items:
            assert item.stock > 0
