from src.domain.chat_store import ChatStore
from src.domain.models.entities import ChatTurn


class NullChatStore(ChatStore):
    """No-op ChatStore - used when SAVE_CONVERSATIONS is off (the default), so local dev and
    tests never need Firestore credentials.
    """

    def save_turn(
        self, session_id: str, message: str, reply: str, history: list[ChatTurn]
    ) -> None:
        pass
