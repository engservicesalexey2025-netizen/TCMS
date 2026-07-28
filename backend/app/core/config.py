from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central runtime configuration, read from environment / .env.

    Switching database backend (local Docker Postgres, native install, or a
    cloud Postgres such as Supabase/Neon) is a one-line change to
    DATABASE_URL — no code changes required.
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    PROJECT_NAME: str = "TCMS"
    API_V1_PREFIX: str = "/api/v1"

    DATABASE_URL: str = (
        "postgresql+psycopg://tcms:tcms@localhost:5432/tcms"
    )

    SECRET_KEY: str = "change-me-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 12
    ALGORITHM: str = "HS256"

    CORS_ORIGINS: list[str] = ["http://localhost:5173"]

    FILE_STORAGE_PATH: str = "./storage"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
