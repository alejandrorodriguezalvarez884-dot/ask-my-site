from pathlib import Path

from fastapi.testclient import TestClient

from app import create_app
from src.domain.models.entities import ChatTurn
from src.infrastructure.settings import Settings


class _StubAssistant:
    """Stands in for ClaudeAssistant so tests never make a real Anthropic API call."""

    def reply(self, system_prompt: str, history: list[ChatTurn], question: str) -> str:
        return f"stub reply to: {question}"


def _make_client(tmp_path: Path) -> TestClient:
    site_yaml = tmp_path / "site.yaml"
    site_yaml.write_text("name: Test Person\nrole: Tester\nabout: Just a test.\n")
    context_dir = tmp_path / "context"
    context_dir.mkdir()
    (context_dir / "notes.md").write_text("Test Person's favorite color is blue.")

    settings = Settings(
        anthropic_api_key="test-key",
        site_config_path=site_yaml,
        context_dir=context_dir,
    )
    app = create_app(settings)
    app.state.assistant = _StubAssistant()
    return TestClient(app)


def test_health(tmp_path: Path) -> None:
    client = _make_client(tmp_path)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_chat_returns_a_reply(tmp_path: Path) -> None:
    client = _make_client(tmp_path)

    response = client.post("/chat", json={"message": "Who are you?"})

    assert response.status_code == 200
    assert response.json()["reply"] == "stub reply to: Who are you?"


def test_chat_rejects_empty_message(tmp_path: Path) -> None:
    client = _make_client(tmp_path)

    response = client.post("/chat", json={"message": ""})

    assert response.status_code == 422
