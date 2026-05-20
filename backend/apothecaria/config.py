from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="APOTHECARIA_", env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./apothecaria.sqlite"
    customer_arrival_seconds: int = 3
    use_agent_customers: bool = False
    use_canned_agent: bool = False
    api_base_url: str = "http://localhost:8000"


settings = Settings()
