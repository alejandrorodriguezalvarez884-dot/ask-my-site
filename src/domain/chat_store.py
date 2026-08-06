from abc import ABC, abstractmethod

from src.domain.models.entities import ChatTurn


class ChatStore(ABC):
    """Anything that can persist a finished chat exchange.

    FirestoreChatStore (infrastructure/firestore_chat_store.py) is the real implementation;
    NullChatStore (infrastructure/null_chat_store.py) is the default when persistence isn't
    enabled, so ChatRepository never has to branch on whether saving is turned on.
    """

    @abstractmethod
    def save_turn(
        self, session_id: str, message: str, reply: str, history: list[ChatTurn]
    ) -> None: ...
