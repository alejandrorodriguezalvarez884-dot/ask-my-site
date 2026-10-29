import logging
import tempfile
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.controllers import router
from src.infrastructure.bm25_retriever import BM25Retriever
from src.infrastructure.context_loader import load_context_documents
from src.infrastructure.firestore_chat_store import FirestoreChatStore
from src.infrastructure.gcs_content import download_content
from src.infrastructure.llm_client import ClaudeAssistant
from src.infrastructure.logging_config import configure_logging
from src.infrastructure.null_chat_store import NullChatStore
from src.infrastructure.settings import Settings
from src.infrastructure.site_config_loader import load_site_config

logger = logging.getLogger(__name__)


def create_app(settings: Settings | None = None) -> FastAPI:
    """App factory - settings can be injected (see tests/test_routes.py) instead of being
    read from the environment, so tests never need a real .env or a real Anthropic key.
    """
    configure_logging()
    settings = settings or Settings()

    app = FastAPI(title="ask-my-site")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins_list,
        allow_methods=["POST", "GET"],
        allow_headers=["*"],
    )

    site_config_path, context_dir = _content_paths(settings)
    site_config = load_site_config(site_config_path)
    chunks = load_context_documents(context_dir)
    retriever = BM25Retriever()
    retriever.index(chunks)
    logger.info("Indexed %d context chunk(s) from %s", len(chunks), context_dir)

    app.state.settings = settings
    app.state.site_config = site_config
    app.state.retriever = retriever
    app.state.assistant = ClaudeAssistant(
        api_key=settings.anthropic_api_key, model=settings.anthropic_model
    )
    app.state.chat_store = (
        FirestoreChatStore(collection=settings.chat_store_collection)
        if settings.save_conversations
        else NullChatStore()
    )

    app.include_router(router)
    return app


def _content_paths(settings: Settings) -> tuple[Path, Path]:
    """Where to read site.yaml and context/ from: the local paths, or a fresh download of
    the content bucket when one is configured (Cloud Run)."""
    if not settings.content_bucket:
        return settings.site_config_path, settings.context_dir

    root = Path(tempfile.mkdtemp(prefix="ask-my-site-content-"))
    count = download_content(settings.content_bucket, root)
    logger.info(
        "Downloaded %d content file(s) from gs://%s", count, settings.content_bucket
    )
    return root / "config" / "site.yaml", root / "context"


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(create_app(), host="0.0.0.0", port=8000)
