import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from apothecaria.db.models import Ingredient, PlayerInventory, PlayerState, StoreItem
from apothecaria.db.seed import seed_database
from apothecaria.domain.store import (
    PurchaseError,
    UnknownIngredientError,
    list_store,
    purchase,
)


@pytest.fixture
def seeded_session(db_engine, db_session):
    with db_engine.connect() as conn:
        seed_database(conn)
    return db_session


def _set_money(session: Session, amount: int) -> None:
    state = session.get(PlayerState, 1)
    assert state is not None
    state.money = amount
    session.flush()


def test_list_store_returns_all_store_items(seeded_session):
    items = list_store(seeded_session)
    assert {item.slug for item in items} == {
        "moonpetal",
        "mushroom",
        "root",
        "feather",
        "eye-of-newt",
        "sage",
    }
    moonpetal = next(item for item in items if item.slug == "moonpetal")
    assert moonpetal.price == 5
    assert moonpetal.stock == 50
    assert moonpetal.name


def test_purchase_charges_the_player(seeded_session):
    _set_money(seeded_session, 50)
    result = purchase(seeded_session, "moonpetal", 3)
    assert result.unit_price == 5
    assert result.total_cost == 15
    assert result.new_money == 35
    assert seeded_session.get(PlayerState, 1).money == 35


def test_purchase_adds_to_player_inventory(seeded_session):
    _set_money(seeded_session, 100)
    moon_id = seeded_session.scalar(select(Ingredient.id).where(Ingredient.slug == "moonpetal"))
    before = seeded_session.get(PlayerInventory, moon_id).quantity
    result = purchase(seeded_session, "moonpetal", 4)
    assert result.new_quantity_owned == before + 4
    assert seeded_session.get(PlayerInventory, moon_id).quantity == before + 4


def test_purchase_reduces_store_stock(seeded_session):
    _set_money(seeded_session, 100)
    result = purchase(seeded_session, "moonpetal", 10)
    item = seeded_session.scalar(
        select(StoreItem).join(StoreItem.ingredient).where(Ingredient.slug == "moonpetal")
    )
    assert item.stock == 40
    assert result.remaining_stock == 40


def test_purchase_insufficient_funds_raises(seeded_session):
    _set_money(seeded_session, 4)
    with pytest.raises(PurchaseError):
        purchase(seeded_session, "moonpetal", 1)


def test_purchase_out_of_stock_raises(seeded_session):
    _set_money(seeded_session, 100_000)
    with pytest.raises(PurchaseError):
        purchase(seeded_session, "moonpetal", 9999)


def test_purchase_unknown_ingredient_raises(seeded_session):
    _set_money(seeded_session, 100)
    with pytest.raises(UnknownIngredientError):
        purchase(seeded_session, "dragon-scale", 1)


def test_purchase_rejects_non_positive_quantity(seeded_session):
    _set_money(seeded_session, 100)
    with pytest.raises(PurchaseError):
        purchase(seeded_session, "moonpetal", 0)
