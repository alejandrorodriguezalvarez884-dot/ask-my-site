import logging
from datetime import UTC, datetime

from google.cloud import firestore

from src.domain.chat_store import ChatStore
from src.domain.models.entities import ChatTurn

logger = logging.getLogger(__name__)


class FirestoreChatStore(ChatStore):
    """Persists each chat exchange to Firestore.

    The API is stateless - the caller resends the full history on every request - so each
    write stores the message, the reply, and the history it was answered against. The last
    write of a browser session therefore holds the fullest transcript; there's no
    session id to key on since the frontend doesn't send one today.

    Uses Application Default Credentials, so no key file or project id to configure: on Cloud
    Run this picks up the service's own project and identity automatically.
    """

    def __init__(self, collection: str) -> None:
        self._collection = firestore.Client().collection(collection)

    def save_turn(self, message: str, reply: str, history: list[ChatTurn]) -> None:
        try:
            self._collection.add(
                {
                    "message": message,
                    "reply": reply,
                    "history": [turn.model_dump() for turn in history],
                    "created_at": datetime.now(UTC),
                }
            )
        except Exception:
            # A persistence failure shouldn't take down the chat feature itself.
            logger.exception("Failed to save conversation turn to Firestore")
