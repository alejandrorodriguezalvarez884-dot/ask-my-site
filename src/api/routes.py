from fastapi import APIRouter, Request

from api.schemas import ChatRequest, ChatResponse
from assistant.persona import build_system_prompt

router = APIRouter()


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/chat", response_model=ChatResponse)
def chat(payload: ChatRequest, request: Request) -> ChatResponse:
    settings = request.app.state.settings
    site_config = request.app.state.site_config
    retriever = request.app.state.retriever
    assistant = request.app.state.assistant

    context_chunks = retriever.search(payload.message, top_k=settings.top_k)
    system_prompt = build_system_prompt(site_config, context_chunks)
    reply = assistant.reply(system_prompt, payload.history, payload.message)

    return ChatResponse(reply=reply)
