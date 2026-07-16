from sqlalchemy import Engine
from sqlalchemy.orm import Session

from apothecaria.db.models import PlayerState
from apothecaria.db.seed import seed_database


def _seed(db_engine: Engine) -> None:
    with db_engine.connect() as conn:
        seed_database(conn)


def _set_money(db_engine: Engine, amount: int) -> None:
    with Session(db_engine) as session:
        state = session.get(PlayerState, 1)
        assert state is not None
        state.money = amount
        session.commit()


def test_get_store_lists_items(client, db_engine):
    _seed(db_engine)
    response = client.get("/api/store")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 6
    moonpetal = next(item for item in data if item["slug"] == "moonpetal")
    assert moonpetal["price"] == 5
    assert moonpetal["stock"] == 50
    assert set(moonpetal.keys()) == {"slug", "name", "price", "stock"}


def test_buy_succeeds_and_reports_new_balance(client, db_engine):
    _seed(db_engine)
    _set_money(db_engine, 50)
    response = client.post("/api/store/buy", json={"ingredient_slug": "moonpetal", "quantity": 3})
    assert response.status_code == 200
    body = response.json()
    assert body["total_cost"] == 15
    assert body["new_money"] == 35
    assert body["ingredient_slug"] == "moonpetal"


def test_buy_unknown_ingredient_returns_404(client, db_engine):
    _seed(db_engine)
    _set_money(db_engine, 100)
    response = client.post(
        "/api/store/buy", json={"ingredient_slug": "dragon-scale", "quantity": 1}
    )
    assert response.status_code == 404
    assert "dragon-scale" in response.json()["detail"]


def test_buy_insufficient_funds_returns_409(client, db_engine):
    _seed(db_engine)
    _set_money(db_engine, 1)
    response = client.post("/api/store/buy", json={"ingredient_slug": "moonpetal", "quantity": 1})
    assert response.status_code == 409


def test_buy_out_of_stock_returns_409(client, db_engine):
    _seed(db_engine)
    _set_money(db_engine, 100_000)
    response = client.post(
        "/api/store/buy", json={"ingredient_slug": "moonpetal", "quantity": 9999}
    )
    assert response.status_code == 409


def test_buy_zero_quantity_returns_422(client, db_engine):
    _seed(db_engine)
    response = client.post("/api/store/buy", json={"ingredient_slug": "moonpetal", "quantity": 0})
    assert response.status_code == 422
