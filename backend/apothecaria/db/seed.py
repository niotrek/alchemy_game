from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sqlalchemy import Connection, select
from sqlalchemy.orm import Session

from apothecaria.db.models import (
    Ingredient,
    PlayerInventory,
    PlayerState,
    Recipe,
    RecipeIngredient,
    StoreItem,
)
from apothecaria.domain.models import IngredientSeed, RecipeSeed, StoreSeed

CONTENT_DIR = Path(__file__).resolve().parents[1] / "content"


def _load_json(name: str) -> list[dict[str, Any]]:
    data: list[dict[str, Any]] = json.loads((CONTENT_DIR / name).read_text())
    return data


def seed_database(connection: Connection) -> None:
    """Idempotently load content JSON into the DB.

    Uses **upsert semantics**: existing rows (matched by slug) are updated
    to match the JSON. This matters during the workshop — students edit
    these files in Module 1 and expect ``make seed`` to reflect changes.
    """
    with Session(bind=connection) as session:
        _seed_ingredients(session)
        _seed_recipes(session)
        _seed_player_state(session)
        _seed_player_inventory(session)
        _seed_store(session)
        session.commit()


def _seed_ingredients(session: Session) -> None:
    rows = [IngredientSeed.model_validate(r) for r in _load_json("ingredients.json")]
    existing = {i.slug: i for i in session.scalars(select(Ingredient)).all()}
    for row in rows:
        if row.slug in existing:
            ing = existing[row.slug]
            ing.name = row.name
            ing.lore = row.lore
            ing.sprite = row.sprite
        else:
            session.add(Ingredient(**row.model_dump()))
    session.flush()


def _seed_recipes(session: Session) -> None:
    rows = [RecipeSeed.model_validate(r) for r in _load_json("recipes.json")]
    by_slug = {i.slug: i for i in session.scalars(select(Ingredient)).all()}
    existing = {r.slug: r for r in session.scalars(select(Recipe)).all()}
    for row in rows:
        if row.slug in existing:
            recipe = existing[row.slug]
            recipe.name = row.name
            recipe.ailment_category = row.ailment_category
            recipe.lore = row.lore
            recipe.sprite = row.sprite
            recipe.ingredient_links.clear()
            session.flush()
            recipe.ingredient_links = [
                RecipeIngredient(ingredient_id=by_slug[s].id) for s in row.ingredients
            ]
        else:
            recipe = Recipe(
                slug=row.slug,
                name=row.name,
                ailment_category=row.ailment_category,
                lore=row.lore,
                sprite=row.sprite,
            )
            recipe.ingredient_links = [
                RecipeIngredient(ingredient_id=by_slug[s].id) for s in row.ingredients
            ]
            session.add(recipe)
    session.flush()


STARTING_MONEY = 100


def _seed_player_state(session: Session) -> None:
    if session.get(PlayerState, 1) is None:
        session.add(PlayerState(id=1, money=STARTING_MONEY, brews_count=0))
        session.flush()


STARTING_QUANTITY = 20


def _seed_player_inventory(session: Session) -> None:
    """Give the player a generous starting stock of every ingredient.

    Use this when seeding a fresh or reset database.
    """
    ingredients = session.scalars(select(Ingredient)).all()
    existing = {pi.ingredient_id for pi in session.scalars(select(PlayerInventory)).all()}
    for ing in ingredients:
        if ing.id in existing:
            continue
        session.add(PlayerInventory(ingredient_id=ing.id, quantity=STARTING_QUANTITY))
    session.flush()


def _seed_store(session: Session) -> None:
    """Load store prices and stock from content/store.json.

    Use this when seeding a fresh or reset database.
    """
    rows = [StoreSeed.model_validate(r) for r in _load_json("store.json")]
    by_slug = {i.slug: i for i in session.scalars(select(Ingredient)).all()}
    existing = {si.ingredient_id: si for si in session.scalars(select(StoreItem)).all()}
    for row in rows:
        ing = by_slug[row.ingredient_slug]
        if ing.id in existing:
            item = existing[ing.id]
            item.price = row.price
            item.stock = row.stock
        else:
            session.add(StoreItem(ingredient_id=ing.id, price=row.price, stock=row.stock))
    session.flush()


def main() -> None:
    """CLI entry: ``python -m apothecaria.db.seed``."""
    from apothecaria.db.session import engine, init_db

    init_db()
    with engine.connect() as conn:
        seed_database(conn)
    print("Database seeded.")


if __name__ == "__main__":
    main()
