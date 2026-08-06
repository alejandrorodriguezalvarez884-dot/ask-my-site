from fastapi import APIRouter, Request

from src.domain.models.entities import ChatRequest, ChatResponse
from src.domain.repositories.chat_repository import ChatRepository
from src.service_layer.chat_service import ChatService

router = APIRouter()


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/chat", response_model=ChatResponse)
def chat(payload: ChatRequest, request: Request) -> ChatResponse:
    settings = request.app.state.settings
    repository = ChatRepository(
        retriever=request.app.state.retriever,
        assistant=request.app.state.assistant,
        chat_store=request.app.state.chat_store,
        site_config=request.app.state.site_config,
        top_k=settings.top_k,
    )
    service = ChatService(repository)
    return service.answer(payload)
