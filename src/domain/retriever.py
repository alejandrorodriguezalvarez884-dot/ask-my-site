from abc import ABC, abstractmethod

from src.domain.models.entities import Chunk


class Retriever(ABC):
    """Anything that can index Chunks and answer similarity queries over them.

    BM25Retriever (infrastructure/bm25_retriever.py) is the only implementation today - swap
    in an embedding-based one later if the context grows large enough that lexical overlap
    stops being a good relevance proxy, without touching anything that calls this interface.
    """

    @abstractmethod
    def index(self, chunks: list[Chunk]) -> None: ...

    @abstractmethod
    def search(self, query: str, top_k: int) -> list[Chunk]: ...
