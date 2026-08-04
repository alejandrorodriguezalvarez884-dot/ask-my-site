from src.domain.models.entities import Chunk
from src.infrastructure.bm25_retriever import BM25Retriever


def test_search_ranks_the_relevant_chunk_first() -> None:
    # BM25's IDF term degenerates toward zero on a corpus this tiny when a query shares only
    # words that appear in just one *other* doc too, so this uses enough chunks - and query
    # vocabulary distinctive enough to just one of them - for a genuine positive score, not a
    # tie broken only by insertion order.
    retriever = BM25Retriever()
    retriever.index(
        [
            Chunk(
                text="The personal website was built with Astro and Tailwind CSS, deployed on GitHub Pages.",
                source="a.md",
            ),
            Chunk(text="I enjoy hiking and playing chess on weekends.", source="b.md"),
            Chunk(
                text="KD Boundaries is a knowledge distillation lab comparing decision boundaries.",
                source="c.md",
            ),
            Chunk(
                text="LLM Router decomposes prompts into subtasks and routes them to cheaper models.",
                source="d.md",
            ),
        ]
    )

    results = retriever.search(
        "What frontend framework was the personal website built with?", top_k=1
    )

    assert results[0].source == "a.md"


def test_search_returns_empty_list_before_indexing() -> None:
    assert BM25Retriever().search("anything", top_k=5) == []


def test_search_respects_top_k() -> None:
    retriever = BM25Retriever()
    retriever.index(
        [
            Chunk(text=f"chunk about python number {i}", source=f"{i}.md")
            for i in range(10)
        ]
    )

    assert len(retriever.search("python", top_k=3)) == 3
