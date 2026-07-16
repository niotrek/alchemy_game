from apothecaria.db.seed import seed_database


def test_next_returns_204_when_no_customer(client, db_engine):
    with db_engine.connect() as conn:
        seed_database(conn)
    response = client.get("/api/customers/next")
    assert response.status_code == 204


def test_spawn_then_next(client, db_engine):
    with db_engine.connect() as conn:
        seed_database(conn)
    spawn = client.post("/api/customers/spawn")
    assert spawn.status_code == 201
    next_resp = client.get("/api/customers/next")
    assert next_resp.status_code == 200
    body = next_resp.json()
    assert "id" in body and "name" in body and "ailment_narrative" in body


def test_serve_returns_outcome_and_removes_customer(client, db_engine):
    with db_engine.connect() as conn:
        seed_database(conn)
    customer = client.post("/api/customers/spawn").json()
    response = client.post(
        f"/api/customers/{customer['id']}/serve",
        json={"ingredient_slugs": ["moonpetal", "feather"]},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["outcome"] in {"delighted", "neutral", "disappointed", "confused"}
    assert "money_delta" in body and "new_money" in body
    next_resp = client.get("/api/customers/next")
    assert next_resp.status_code == 204


def test_serve_unknown_customer_returns_404(client, db_engine):
    with db_engine.connect() as conn:
        seed_database(conn)
    response = client.post(
        "/api/customers/nonexistent-id/serve",
        json={"ingredient_slugs": ["moonpetal"]},
    )
    assert response.status_code == 404


def test_serve_twice_returns_404_second_time(client, db_engine):
    with db_engine.connect() as conn:
        seed_database(conn)
    customer = client.post("/api/customers/spawn").json()
    body = {"ingredient_slugs": ["moonpetal", "sage", "root"]}
    client.post(f"/api/customers/{customer['id']}/serve", json=body)
    response = client.post(f"/api/customers/{customer['id']}/serve", json=body)
    assert response.status_code == 404
