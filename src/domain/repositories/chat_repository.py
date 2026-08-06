from src.domain.chat_store import ChatStore
from src.domain.models.entities import ChatTurn, SiteConfig
from src.domain.persona import build_system_prompt
from src.domain.retriever import Retriever
from src.infrastructure.llm_client import ClaudeAssistant


class ChatRepository:
    """Combines context retrieval, persona/prompt assembly, and the LLM call - the same role
    reference implementations give a "repository": business logic plus calls to
    infrastructure, kept out of both the controller and the service layer.
    """

    def __init__(
        self,
        retriever: Retriever,
        assistant: ClaudeAssistant,
        chat_store: ChatStore,
        site_config: SiteConfig,
        top_k: int,
    ) -> None:
        self._retriever = retriever
        self._assistant = assistant
        self._chat_store = chat_store
        self._site_config = site_config
        self._top_k = top_k

    def get_reply(self, message: str, history: list[ChatTurn]) -> str:
        context_chunks = self._retriever.search(message, top_k=self._top_k)
        system_prompt = build_system_prompt(self._site_config, context_chunks)
        reply = self._assistant.reply(system_prompt, history, message)
        self._chat_store.save_turn(message, reply, history)
        return reply
