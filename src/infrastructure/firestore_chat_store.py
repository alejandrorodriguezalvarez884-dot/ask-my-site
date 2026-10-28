import logging
from datetime import UTC, datetime

from google.cloud import firestore

from src.domain.chat_store import ChatStore
from src.domain.models.entities import ChatTurn

logger = logging.getLogger(__name__)

_PREVIEW_LENGTH = 100


def _preview(text: str) -> str:
    """First-message summary shown as a column in the Firestore console's table view, so a
    conversation is recognizable without opening its document.
    """
    text = " ".join(text.split())
    return text if len(text) <= _PREVIEW_LENGTH else text[: _PREVIEW_LENGTH - 1].rstrip() + "…"


class FirestoreChatStore(ChatStore):
    """Persists each chat exchange to Firestore, one document per conversation.

    The API is stateless - the caller resends the full history on every request - so each
    save just upserts the document keyed by session_id: the full transcript (history plus
    this new exchange) replaces the previous one. A session's document is stable and grows in
    place instead of each turn scattering a new document, which is what happened before
    session_id existed.

    Besides `history`, each document carries fields chosen so the collection is readable
    straight from the Firestore console's default table view, with no document opened:
    `preview` (the opening message, so you can tell conversations apart at a glance),
    `turn_count` (a quick read on how long it ran), and `created_at`/`updated_at` (real
    Firestore timestamps - the console can sort a column on either with one click, no
    composite index needed since it's a single-field sort).

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
            existing_data = existing.to_dict() if existing.exists else {}
            now = datetime.now(UTC)
            full_history = [
                *history,
                ChatTurn(role="user", content=message),
                ChatTurn(role="assistant", content=reply),
            ]
            doc_ref.set(
                {
                    "history": [turn.model_dump() for turn in full_history],
                    "preview": existing_data.get("preview") or _preview(message),
                    "turn_count": len(full_history),
                    "created_at": existing_data.get("created_at") or now,
                    "updated_at": now,
                }
            )
        except Exception:
            # A persistence failure shouldn't take down the chat feature itself.
            logger.exception("Failed to save conversation turn to Firestore")
