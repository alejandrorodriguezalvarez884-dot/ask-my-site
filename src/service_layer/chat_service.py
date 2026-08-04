from src.domain.models.entities import ChatRequest, ChatResponse
from src.domain.repositories.chat_repository import ChatRepository


class ChatService:
    """Service layer that acts as an intermediary between the controller and the repository.
    It handles the request/response DTOs: unpacking requests and packing responses.
    """

    def __init__(self, repository: ChatRepository) -> None:
        self._repository = repository

    def answer(self, request: ChatRequest) -> ChatResponse:
        reply = self._repository.get_reply(request.message, request.history)
        return ChatResponse(reply=reply)
