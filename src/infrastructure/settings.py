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
    # When set, config/site.yaml and context/ are downloaded from this Cloud Storage bucket
    # at startup instead of read from the two local paths above (see gcs_content.py). Set on
    # Cloud Run by deploy.sh; left empty locally so dev and tests stay offline.
    content_bucket: str = ""
    top_k: int = 5

    # Off by default so local dev/tests never need Firestore credentials. When on, each chat
    # exchange is written to the Firestore collection below via Application Default
    # Credentials (see src/infrastructure/firestore_chat_store.py).
    save_conversations: bool = False
    chat_store_collection: str = "conversations"

    @property
    def allowed_origins_list(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.allowed_origins.split(",")
            if origin.strip()
        ]
