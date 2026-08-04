import re

from rank_bm25 import BM25Okapi

from src.domain.models.entities import Chunk
from src.domain.retriever import Retriever

_TOKEN_RE = re.compile(r"[a-zA-Z0-9]+")


def _tokenize(text: str) -> list[str]:
    return _TOKEN_RE.findall(text.lower())


class BM25Retriever(Retriever):
    """Lexical (keyword-overlap) retriever - the default Retriever implementation.

    Deliberately not embedding-based: for the handful of documents a personal or small-
    business site's assistant realistically needs, BM25 is good enough and needs no model
    download, no vector store, and no extra infrastructure - the same "don't reach for a
    heavy stack when a simple one covers the real use case" call made in custom-llm-finetuning.
    """

    def __init__(self) -> None:
        self._chunks: list[Chunk] = []
        self._bm25: BM25Okapi | None = None

    def index(self, chunks: list[Chunk]) -> None:
        self._chunks = chunks
        tokenized = [_tokenize(chunk.text) for chunk in chunks]
        self._bm25 = BM25Okapi(tokenized) if tokenized else None

    def search(self, query: str, top_k: int) -> list[Chunk]:
        if self._bm25 is None:
            return []
        scores = self._bm25.get_scores(_tokenize(query))
        ranked = sorted(
            zip(scores, self._chunks, strict=True),
            key=lambda pair: pair[0],
            reverse=True,
        )
        return [chunk for score, chunk in ranked[:top_k] if score > 0]
