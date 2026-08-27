from functools import lru_cache

from pydantic_settings import SettingsConfigDict
from zarreh_agentkit.settings import AgentSettings


class Settings(AgentSettings):
    """Application configuration, sourced from the environment."""

    model_config = SettingsConfigDict(env_file=".env", env_prefix="ROUTER_", extra="ignore")

    langsmith_project: str = "disruption-router"

    rulebook_path: str = "data/rulebook.json"
    runs_db_path: str = "data/runs.sqlite"


@lru_cache
def get_settings() -> Settings:
    return Settings()
