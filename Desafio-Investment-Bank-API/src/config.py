from decimal import Decimal
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "sqlite:///./qi.db"
    jwt_secret: str = "development-secret-key-with-at-least-32-bytes"
    mock_base_url: str = "http://localhost:9000"
    spread_rate: Decimal = Decimal("0.025")
    currency_drop_alert_rate: Decimal = Decimal("0.10")
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
