from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from apothecaria.db.models import Ingredient, PlayerInventory, PlayerState, StoreItem
from apothecaria.domain.models import PurchaseResult, StoreItemView


class PurchaseError(Exception):
    """A purchase that cannot be completed. The message is player-facing."""


class UnknownIngredientError(PurchaseError):
    """The requested ingredient slug does not match any ingredient."""


def list_store(session: Session) -> list[StoreItemView]:
    """List every ingredient the store sells, with price and remaining stock.

    Use this to show the player what they can buy.
    :param session: active SQLAlchemy session.
    :return: store items ordered by ingredient name.
    """
    items = session.scalars(
        select(StoreItem).join(StoreItem.ingredient).order_by(Ingredient.name)
    ).all()
    return [
        StoreItemView(
            slug=item.ingredient.slug,
            name=item.ingredient.name,
            price=item.price,
            stock=item.stock,
        )
        for item in items
    ]


def purchase(session: Session, ingredient_slug: str, quantity: int) -> PurchaseResult:
    """Buy ``quantity`` units of an ingredient from the store.

    Decrements store stock and player money, and increments the player's
    inventory. All three changes are flushed together.
    :param session: active SQLAlchemy session.
    :param ingredient_slug: slug of the ingredient to buy.
    :param quantity: how many units to buy; must be at least 1.
    :return: a summary of the completed purchase.
    :raises UnknownIngredientError: the slug matches no ingredient.
    :raises PurchaseError: the quantity is not positive, the ingredient is not
        sold, the store lacks stock, or the player cannot afford it.
    """
    if quantity < 1:
        raise PurchaseError("You must buy at least 1 unit.")

    ingredient = session.scalar(select(Ingredient).where(Ingredient.slug == ingredient_slug))
    if ingredient is None:
        raise UnknownIngredientError(f"No ingredient '{ingredient_slug}' exists.")

    item = session.scalar(select(StoreItem).where(StoreItem.ingredient_id == ingredient.id))
    if item is None:
        raise PurchaseError(f"{ingredient.name} is not sold in the store.")
    if item.stock < quantity:
        raise PurchaseError(
            f"The store only has {item.stock} {ingredient.name} in stock "
            f"(you asked for {quantity})."
        )

    cost = item.price * quantity

    state = session.get(PlayerState, 1)
    if state is None:
        state = PlayerState(id=1, money=0, brews_count=0)
        session.add(state)
        session.flush()
    if state.money < cost:
        raise PurchaseError(
            f"{quantity} {ingredient.name} costs ${cost}, " f"but you only have ${state.money}."
        )

    inventory = session.get(PlayerInventory, ingredient.id)
    if inventory is None:
        inventory = PlayerInventory(ingredient_id=ingredient.id, quantity=0)
        session.add(inventory)

    item.stock -= quantity
    state.money -= cost
    inventory.quantity += quantity
    session.flush()

    return PurchaseResult(
        ingredient_slug=ingredient.slug,
        ingredient_name=ingredient.name,
        quantity=quantity,
        unit_price=item.price,
        total_cost=cost,
        new_money=state.money,
        new_quantity_owned=inventory.quantity,
        remaining_stock=item.stock,
        message=(
            f"Bought {quantity} × {ingredient.name} for ${cost}. " f"Balance: ${state.money}."
        ),
    )
