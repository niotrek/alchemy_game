from apothecaria.db.seed import seed_database


def test_recipes_returns_five(client, db_engine):
    with db_engine.connect() as conn:
        seed_database(conn)
    response = client.get("/api/recipes")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 5
    slugs = {r["slug"] for r in data}
    assert {"sleep_draught", "energy_elixir", "calming_tonic", "healing_balm", "fog_veil"} == slugs


def test_recipe_lists_ingredients(client, db_engine):
    with db_engine.connect() as conn:
        seed_database(conn)
    response = client.get("/api/recipes")
    sleep = next(r for r in response.json() if r["slug"] == "sleep_draught")
    assert set(sleep["ingredient_slugs"]) == {"moonpetal", "sage", "root"}
