from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from apothecaria.db.models import Ingredient, PlayerIngredient, Recipe
from apothecaria.domain.models import BrewResult


def combine_ingredients(ingredient_slugs: list[str], session: Session) -> BrewResult:
    if not ingredient_slugs:
        return BrewResult(
            matched_recipe_slug=None,
            matched_recipe_name=None,
            matched_ailment_category=None,
            quality_score=0.0,
            ingredient_slugs=[],
            description="An empty cauldron sits cold.",
        )

    requested = list(ingredient_slugs)
    requested_set = set(requested)

    known = {
        i.slug
        for i in session.scalars(select(Ingredient).where(Ingredient.slug.in_(requested))).all()
    }
    unknown = requested_set - known
    if unknown:
        return BrewResult(
            matched_recipe_slug=None,
            matched_recipe_name=None,
            matched_ailment_category=None,
            quality_score=0.0,
            ingredient_slugs=requested,
            description=f"The cauldron sputters at unknown ingredients: {sorted(unknown)}.",
        )

    # Check player has enough of each ingredient
    insufficient = _check_quantities(requested, session)
    if insufficient:
        return BrewResult(
            matched_recipe_slug=None,
            matched_recipe_name=None,
            matched_ailment_category=None,
            quality_score=0.0,
            ingredient_slugs=requested,
            description=insufficient,
        )

    # Decrement ingredient quantities
    _consume_ingredients(requested, session)

    for recipe in session.scalars(select(Recipe)).all():
        recipe_slugs = {link.ingredient.slug for link in recipe.ingredient_links}
        if recipe_slugs == requested_set and len(requested) == len(recipe_slugs):
            return BrewResult(
                matched_recipe_slug=recipe.slug,
                matched_recipe_name=recipe.name,
                matched_ailment_category=recipe.ailment_category,
                quality_score=1.0,
                ingredient_slugs=requested,
                description=f"The brew settles into a perfect {recipe.name.lower()}.",
            )

    return BrewResult(
        matched_recipe_slug=None,
        matched_recipe_name=None,
        matched_ailment_category=None,
        quality_score=0.0,
        ingredient_slugs=requested,
        description="The cauldron belches a foul-smelling cloud — an unknown brew.",
    )


def _check_quantities(slugs: list[str], session: Session) -> str | None:
    """Return an error message if any ingredient is insufficient, else None."""
    slug_counts: dict[str, int] = {}
    for s in slugs:
        slug_counts[s] = slug_counts.get(s, 0) + 1

    inventory = {
        pi.ingredient_slug: pi.quantity
        for pi in session.scalars(
            select(PlayerIngredient).where(PlayerIngredient.ingredient_slug.in_(list(slug_counts)))
        ).all()
    }

    missing: list[str] = []
    for slug, needed in slug_counts.items():
        have = inventory.get(slug, 0)
        if have < needed:
            missing.append(f"{slug} (have {have}, need {needed})")

    if missing:
        return f"Not enough ingredients: {', '.join(missing)}."
    return None


def _consume_ingredients(slugs: list[str], session: Session) -> None:
    """Decrement player quantities for each ingredient used."""
    slug_counts: dict[str, int] = {}
    for s in slugs:
        slug_counts[s] = slug_counts.get(s, 0) + 1

    for pi in session.scalars(
        select(PlayerIngredient).where(PlayerIngredient.ingredient_slug.in_(list(slug_counts)))
    ).all():
        pi.quantity -= slug_counts[pi.ingredient_slug]
    session.flush()
