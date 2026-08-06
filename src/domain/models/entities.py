from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel, Field


class SiteConfig(BaseModel):
    """The assistant's own context: who it's speaking for, loaded from config/site.yaml.

    Independent of context/ - this is fixed persona/identity information, not documents
    to search over.
    """

    name: str
    role: str = ""
    about: str = ""
    tone: str = "friendly and concise"
    links: dict[str, str] = Field(default_factory=dict)


class ChatTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: str


@dataclass(frozen=True)
class Chunk:
    text: str
    # File path relative to the context directory (e.g. "cv.md"), or a fixed label like
    # "site_config" for chunks that came from config/site.yaml instead of a dropped-in file.
    source: str


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    history: list[ChatTurn] = Field(default_factory=list)
    # Optional: the caller (chat widget) should generate one uuid4 per browser conversation
    # and resend it on every request. If omitted, the server mints one and returns it in
    # ChatResponse so a caller that doesn't track sessions still gets a working id back -
    # though since it won't resend it, each of its requests ends up as its own session.
    session_id: str | None = None


class ChatResponse(BaseModel):
    reply: str
    session_id: str
