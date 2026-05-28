from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Database — SQLite (no server required for demo)
    db_path: str = "sitetrack.db"

    # Anthropic
    anthropic_api_key: str = ""

    # Auth
    jwt_secret: str = "sitetrack-demo-secret-change-in-prod"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 480

    # App
    app_env: str = "development"
    cors_origins: str = "http://localhost:5173"

    @property
    def database_url(self) -> str:
        return f"sqlite:///{self.db_path}"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",")]

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
