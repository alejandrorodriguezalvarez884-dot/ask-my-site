from src.domain.chat_store import ChatStore
from src.domain.models.entities import ChatTurn, Chunk, SiteConfig
from src.domain.repositories.chat_repository import ChatRepository
from src.infrastructure.null_chat_store import NullChatStore


class _StubRetriever:
    def index(self, chunks: list[Chunk]) -> None:
        pass

    def search(self, query: str, top_k: int) -> list[Chunk]:
        return []


class _StubAssistant:
    def reply(self, system_prompt: str, history: list[ChatTurn], question: str) -> str:
        return f"stub reply to: {question}"


class _RecordingChatStore(ChatStore):
    def __init__(self) -> None:
        self.saved: list[tuple[str, str, list[ChatTurn]]] = []

    def save_turn(self, message: str, reply: str, history: list[ChatTurn]) -> None:
        self.saved.append((message, reply, history))


def _make_repository(chat_store: ChatStore) -> ChatRepository:
    return ChatRepository(
        retriever=_StubRetriever(),
        assistant=_StubAssistant(),
        chat_store=chat_store,
        site_config=SiteConfig(name="Test Person"),
        top_k=5,
    )


def test_get_reply_saves_the_turn_after_answering() -> None:
    chat_store = _RecordingChatStore()
    repository = _make_repository(chat_store)
    history = [ChatTurn(role="user", content="hi")]

    reply = repository.get_reply("Who are you?", history)

    assert reply == "stub reply to: Who are you?"
    assert chat_store.saved == [("Who are you?", reply, history)]


def test_get_reply_works_with_the_default_null_store() -> None:
    repository = _make_repository(NullChatStore())

    reply = repository.get_reply("Who are you?", [])

    assert reply == "stub reply to: Who are you?"
