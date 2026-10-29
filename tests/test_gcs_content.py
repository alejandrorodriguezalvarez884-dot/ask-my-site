from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import app as app_module
from src.infrastructure.gcs_content import download_content
from src.infrastructure.settings import Settings


class _FakeBlob:
    def __init__(self, name: str, data: str) -> None:
        self.name = name
        self._data = data

    def download_to_filename(self, filename: str) -> None:
        Path(filename).write_text(self._data, encoding="utf-8")


class _FakeClient:
    """Stands in for google.cloud.storage.Client so tests never touch GCP."""

    def __init__(self, blobs: dict[str, str]) -> None:
        self._blobs = blobs

    def list_blobs(self, bucket_name: str) -> list[_FakeBlob]:
        return [_FakeBlob(name, data) for name, data in self._blobs.items()]


def test_downloads_objects_keeping_their_paths(tmp_path: Path) -> None:
    client = _FakeClient(
        {
            "config/site.yaml": "name: Test Person\n",
            "context/": "",  # folder placeholder, skipped
            "context/cv.md": "Worked at a lab.",
            "context/projects/kd.md": "A distillation lab.",
        }
    )

    count = download_content("bucket", tmp_path, client=client)

    assert count == 3
    assert (tmp_path / "config" / "site.yaml").read_text() == "name: Test Person\n"
    assert (tmp_path / "context" / "projects" / "kd.md").exists()


def test_refuses_paths_outside_the_destination(tmp_path: Path) -> None:
    client = _FakeClient({"../escape.md": "nope"})

    with pytest.raises(ValueError):
        download_content("bucket", tmp_path / "dest", client=client)


def test_app_reads_content_from_the_bucket_when_configured(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    client = _FakeClient(
        {
            "config/site.yaml": "name: Bucket Person\nrole: Tester\n",
            "context/notes.md": "Bucket Person's favorite color is green.",
            # BM25's idf is zero or below for a term in half the documents or more, so the
            # matching doc needs a couple of others around it to score at all.
            "context/running.md": "Bucket Person runs half marathons.",
            "context/reading.md": "Bucket Person reads history books.",
        }
    )
    monkeypatch.setattr(
        app_module,
        "download_content",
        lambda bucket, dest: download_content(bucket, dest, client=client),
    )

    settings = Settings(
        anthropic_api_key="test-key",
        content_bucket="my-content",
        # Local paths that don't exist: the app must not fall back to them.
        site_config_path=tmp_path / "missing.yaml",
        context_dir=tmp_path / "missing",
    )
    app = app_module.create_app(settings)

    assert app.state.site_config.name == "Bucket Person"
    chunks = app.state.retriever.search("favorite color", top_k=1)
    assert chunks and "green" in chunks[0].text
    assert TestClient(app).get("/health").status_code == 200
