from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    anthropic_api_key: str
    anthropic_model: str = "claude-sonnet-5"

    # Comma-separated in the environment; see allowed_origins_list.
    allowed_origins: str = "http://localhost:4321"

    site_config_path: Path = Path("config/site.yaml")
    context_dir: Path = Path("context")
    top_k: int = 5

    @property
    def allowed_origins_list(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.allowed_origins.split(",")
            if origin.strip()
        ]
