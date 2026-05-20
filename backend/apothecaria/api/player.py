from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from apothecaria.api.deps import get_session
from apothecaria.db.models import PlayerState

router = APIRouter()


class PlayerOut(BaseModel):
    money: int
    brews_count: int

    model_config = {"from_attributes": True}


@router.get("/api/player", response_model=PlayerOut)
def get_player(session: Session = Depends(get_session)) -> PlayerOut:
    """Return the current player state.

    Use this when the frontend boots and needs the current money balance.
    :param session: DB session injected by FastAPI.
    :return: current player money and brew count.
    """
    state = session.get(PlayerState, 1)
    if state is None:
        return PlayerOut(money=0, brews_count=0)
    return PlayerOut.model_validate(state)
