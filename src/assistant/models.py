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
