from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Multichannel Helpdesk"
    app_env: str = "development"
    api_port: int = 8000

    mongodb_uri: str = "mongodb://localhost:27017"
    mongodb_database: str = "helpdesk_demo"

    jwt_secret: str = "change-me"
    jwt_algorithm: str = "HS256"
    jwt_expires_in: int = 3600
    jwt_refresh_expires_in: int = 604800

    cors_origins: str = "http://localhost:3000"
    demo_mode: bool = True
    webhook_token: str = "demo-webhook-token"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
