from pathlib import Path

from src.infrastructure.context_loader import load_context_documents


def test_loads_and_chunks_markdown_files(tmp_path: Path) -> None:
    (tmp_path / "notes.md").write_text("a" * 1000)
    (tmp_path / "ignored.png").write_bytes(b"\x89PNG")

    chunks = load_context_documents(tmp_path)

    assert all(chunk.source == "notes.md" for chunk in chunks)
    assert (
        len(chunks) > 1
    )  # 1000 chars > CHUNK_SIZE, so it should split into more than one


def test_ignores_non_text_files(tmp_path: Path) -> None:
    (tmp_path / "manual.pdf").write_bytes(b"%PDF-1.7")

    assert load_context_documents(tmp_path) == []


def test_missing_directory_returns_empty_list(tmp_path: Path) -> None:
    assert load_context_documents(tmp_path / "does-not-exist") == []


def test_reads_nested_subdirectories(tmp_path: Path) -> None:
    nested = tmp_path / "projects"
    nested.mkdir()
    (nested / "kd-boundaries.md").write_text("A knowledge distillation lab.")

    chunks = load_context_documents(tmp_path)

    assert len(chunks) == 1
    assert chunks[0].source == str(Path("projects") / "kd-boundaries.md")
