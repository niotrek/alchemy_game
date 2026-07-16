from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from apothecaria.api.deps import get_session
from apothecaria.db.models import Ingredient, PlayerIngredient, PlayerState

router = APIRouter()


class IngredientOut(BaseModel):
    slug: str
    name: str
    lore: str
    sprite: str

    model_config = {"from_attributes": True}


@router.get("/api/inventory", response_model=list[IngredientOut])
def list_inventory(session: Session = Depends(get_session)) -> list[IngredientOut]:
    rows = session.scalars(select(Ingredient).order_by(Ingredient.name)).all()
    return [IngredientOut.model_validate(r) for r in rows]


@router.get("/api/inventory/quantities")
def get_quantities(session: Session = Depends(get_session)) -> dict[str, int]:
    """Return a map of ingredient slug → player quantity."""
    rows = session.scalars(select(PlayerIngredient)).all()
    return {row.ingredient_slug: row.quantity for row in rows}


@router.get("/api/player/money")
def get_money(session: Session = Depends(get_session)) -> dict[str, int]:
    """Return the player's current money."""
    state = session.get(PlayerState, 1)
    return {"money": state.money if state else 0}
