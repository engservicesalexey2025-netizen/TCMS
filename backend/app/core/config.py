from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central runtime configuration, read from environment / .env.

    Switching database backend (local Docker Postgres, native install, or a
    cloud Postgres such as Supabase/Neon) is a one-line change to
    DATABASE_URL — no code changes required.
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    PROJECT_NAME: str = "TSMS"
    API_V1_PREFIX: str = "/api/v1"

    DATABASE_URL: str = (
        "postgresql+psycopg://tcms:tcms@localhost:5432/tcms"
    )

    SECRET_KEY: str = "change-me-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 12
    ALGORITHM: str = "HS256"

    CORS_ORIGINS: list[str] = ["http://localhost:5173"]

    FILE_STORAGE_PATH: str = "./storage"

    # Пусто = локальный диск (см. app/services/file_storage.py) — поведение
    # по умолчанию для локальной разработки. На хостинге с эфемерным диском
    # (например, Render free) задаются все 4 переменные — файлы уходят в
    # S3-совместимое хранилище (например, Cloudflare R2) и переживают редеплой.
    S3_ENDPOINT_URL: str = ""
    S3_ACCESS_KEY_ID: str = ""
    S3_SECRET_ACCESS_KEY: str = ""
    S3_BUCKET_NAME: str = ""

    # Модуль «Управление доступом и безопасностью» (МОДУЛЬ 001)
    LOGIN_LOCKOUT_THRESHOLD: int = 5
    LOGIN_LOCKOUT_MINUTES: int = 15
    PASSWORD_RESET_TOKEN_MINUTES: int = 15
    PASSWORD_HISTORY_LIMIT: int = 5
    PASSWORD_MIN_LENGTH: int = 8
    VIEW_AS_TOKEN_MINUTES: int = 30
    MFA_ISSUER_NAME: str = "TSMS"

    # Пусто = SMTP не настроен: ссылки восстановления пароля показываются
    # администратору в интерфейсе вместо отправки письма (см. план модуля
    # доступа, §1.7 — решение согласовано с заказчиком).
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = ""
    SMTP_USE_TLS: bool = True


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
