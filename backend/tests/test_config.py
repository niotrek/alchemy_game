from apothecaria.config import Settings


def test_default_settings():
    s = Settings()
    assert s.database_url == "sqlite:///./apothecaria.sqlite"
    assert s.customer_arrival_seconds == 30
    assert s.use_agent_customers is False
    assert s.use_canned_agent is False


def test_settings_overrides_from_env(monkeypatch):
    monkeypatch.setenv("APOTHECARIA_DATABASE_URL", "sqlite:///:memory:")
    monkeypatch.setenv("APOTHECARIA_CUSTOMER_ARRIVAL_SECONDS", "5")
    s = Settings()
    assert s.database_url == "sqlite:///:memory:"
    assert s.customer_arrival_seconds == 5


def test_api_base_url_defaults_to_localhost():
    assert Settings().api_base_url == "http://localhost:8000"
