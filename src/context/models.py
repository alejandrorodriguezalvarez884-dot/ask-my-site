from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class Chunk:
    text: str
    # File path relative to the context directory (e.g. "cv.md"), or a fixed label like
    # "site_config" for chunks that came from config/site.yaml instead of a dropped-in file.
    source: str


class Retriever(ABC):
    """Anything that can index Chunks and answer similarity queries over them.

    BM25Retriever (retriever.py) is the only implementation today - swap in an
    embedding-based one later if the context grows large enough that lexical overlap
    stops being a good relevance proxy, without touching anything that calls this interface.
    """

    @abstractmethod
    def index(self, chunks: list[Chunk]) -> None: ...

    @abstractmethod
    def search(self, query: str, top_k: int) -> list[Chunk]: ...
