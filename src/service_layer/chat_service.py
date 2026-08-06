import uuid

from src.domain.models.entities import ChatRequest, ChatResponse
from src.domain.repositories.chat_repository import ChatRepository


class ChatService:
    """Service layer that acts as an intermediary between the controller and the repository.
    It handles the request/response DTOs: unpacking requests and packing responses.
    """

    def __init__(self, repository: ChatRepository) -> None:
        self._repository = repository

    def answer(self, request: ChatRequest) -> ChatResponse:
        # First message of a conversation won't have one yet; mint it here and hand it back
        # so the caller can resend it on every later message in the same conversation.
        session_id = request.session_id or str(uuid.uuid4())
        reply = self._repository.get_reply(session_id, request.message, request.history)
        return ChatResponse(reply=reply, session_id=session_id)
