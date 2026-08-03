from anthropic import Anthropic

from assistant.models import ChatTurn


class ClaudeAssistant:
    """Thin wrapper around the Anthropic API - the only place in this repo that talks to Claude."""

    def __init__(self, api_key: str, model: str) -> None:
        self._client = Anthropic(api_key=api_key)
        self._model = model

    def reply(self, system_prompt: str, history: list[ChatTurn], question: str) -> str:
        messages = [{"role": turn.role, "content": turn.content} for turn in history]
        messages.append({"role": "user", "content": question})

        response = self._client.messages.create(
            model=self._model,
            max_tokens=1024,
            system=system_prompt,
            messages=messages,
        )
        return "".join(block.text for block in response.content if block.type == "text")
