import logging
from datetime import UTC, datetime

from google.cloud import firestore

from src.domain.chat_store import ChatStore
from src.domain.models.entities import ChatTurn

logger = logging.getLogger(__name__)


class FirestoreChatStore(ChatStore):
    """Persists each chat exchange to Firestore, one document per conversation.

    The API is stateless - the caller resends the full history on every request - so each
    save just upserts the document keyed by session_id: the full transcript (history plus
    this new exchange) replaces the previous one, and created_at/updated_at track the
    conversation's lifetime. A session's document is stable and grows in place instead of
    each turn scattering a new document, which is what happened before session_id existed.

    Uses Application Default Credentials, so no key file or project id to configure: on Cloud
    Run this picks up the service's own project and identity automatically.
    """

    def __init__(self, collection: str) -> None:
        self._collection = firestore.Client().collection(collection)

    def save_turn(
        self, session_id: str, message: str, reply: str, history: list[ChatTurn]
    ) -> None:
        try:
            doc_ref = self._collection.document(session_id)
            existing = doc_ref.get()
            created_at = existing.get("created_at") if existing.exists else None
            now = datetime.now(UTC)
            full_history = [
                *history,
                ChatTurn(role="user", content=message),
                ChatTurn(role="assistant", content=reply),
            ]
            doc_ref.set(
                {
                    "history": [turn.model_dump() for turn in full_history],
                    "created_at": created_at or now,
                    "updated_at": now,
                }
            )
        except Exception:
            # A persistence failure shouldn't take down the chat feature itself.
            logger.exception("Failed to save conversation turn to Firestore")
