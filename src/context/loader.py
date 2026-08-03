from pathlib import Path

from context.models import Chunk

# Plain-text formats only for now - a PDF/HTML loader can be added here later without
# touching anything downstream, since everything past this module only deals in Chunks.
TEXT_SUFFIXES = {".md", ".txt"}

CHUNK_SIZE = 800  # characters
CHUNK_OVERLAP = 100


def load_context_documents(context_dir: Path) -> list[Chunk]:
    """Reads every .md/.txt file under context_dir (recursively) and splits it into Chunks.

    Returns an empty list if the directory doesn't exist yet - a fresh clone of this
    template has nothing in context/ besides .gitkeep, and that's a valid starting state,
    not an error.
    """
    if not context_dir.exists():
        return []

    chunks: list[Chunk] = []
    for path in sorted(context_dir.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        chunks.extend(_chunk_text(text, source=str(path.relative_to(context_dir))))
    return chunks


def _chunk_text(text: str, source: str) -> list[Chunk]:
    text = text.strip()
    if not text:
        return []

    chunks: list[Chunk] = []
    start = 0
    while start < len(text):
        end = start + CHUNK_SIZE
        chunks.append(Chunk(text=text[start:end], source=source))
        if end >= len(text):
            break
        start = end - CHUNK_OVERLAP
    return chunks
