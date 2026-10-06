from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AI Mind Clone"
    app_env: str = "development"
    database_url: str = "sqlite:///./data/ai_mind_clone.db"
    owner_username: str | None = None
    owner_password: str | None = None
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
