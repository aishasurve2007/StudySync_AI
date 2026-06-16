"""
Central configuration.

Everything the app needs comes from environment variables, parsed and
validated once here via pydantic-settings. The rest of the code imports
`settings` and never reads os.environ directly — so there is a single,
typed source of truth and missing/garbage config fails loudly at startup.
"""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Database
    DATABASE_URL: str = "postgresql://studysync:studysync@localhost:5432/studysync"

    # Auth
    JWT_SECRET: str = "change-me"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080  # 7 days

    # AI (used from chunk 3 onward; defaults keep the app running with no key)
    AI_PROVIDER: str = "none"
    OPENAI_API_KEY: str | None = None
    GEMINI_API_KEY: str | None = None

    # CORS
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    # lru_cache => parsed exactly once per process.
    return Settings()


settings = get_settings()
