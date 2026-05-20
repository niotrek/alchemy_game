from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from apothecaria.api.deps import get_session
from apothecaria.domain.models import PurchaseResult, StoreItemView
from apothecaria.domain.store import (
    PurchaseError,
    UnknownIngredientError,
    list_store,
    purchase,
)

router = APIRouter()


class BuyBody(BaseModel):
    ingredient_slug: str = Field(min_length=1)
    quantity: int = Field(ge=1)


@router.get("/api/store", response_model=list[StoreItemView])
def get_store(session: Session = Depends(get_session)) -> list[StoreItemView]:
    """List every ingredient the store sells, with price and stock.

    Use this to show the player what they can buy.
    :param session: DB session injected by FastAPI.
    :return: store items ordered by ingredient name.
    """
    return list_store(session)


@router.post("/api/store/buy", response_model=PurchaseResult)
def buy(body: BuyBody, session: Session = Depends(get_session)) -> PurchaseResult:
    """Buy an ingredient from the store.

    :param body: the ingredient slug and quantity to buy.
    :param session: DB session injected by FastAPI.
    :return: a summary of the completed purchase.
    :raises HTTPException: 404 if the ingredient is unknown, 409 if the
        purchase cannot be completed (out of stock, insufficient funds).
    """
    try:
        return purchase(session, body.ingredient_slug, body.quantity)
    except UnknownIngredientError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PurchaseError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
