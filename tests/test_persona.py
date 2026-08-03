from assistant.models import SiteConfig
from assistant.persona import build_system_prompt
from context.models import Chunk


def test_prompt_includes_name_role_and_context() -> None:
    site = SiteConfig(
        name="Alex", role="Engineer", about="Builds things.", tone="friendly"
    )
    chunks = [Chunk(text="Alex's favorite language is Python.", source="cv.md")]

    prompt = build_system_prompt(site, chunks)

    assert "Alex" in prompt
    assert "Engineer" in prompt
    assert "favorite language is Python" in prompt


def test_prompt_includes_links_when_present() -> None:
    site = SiteConfig(name="Alex", links={"GitHub": "https://github.com/alex"})

    prompt = build_system_prompt(site, context_chunks=[])

    assert "https://github.com/alex" in prompt


def test_prompt_omits_context_section_when_nothing_retrieved() -> None:
    site = SiteConfig(name="Alex")

    prompt = build_system_prompt(site, context_chunks=[])

    assert "Relevant context" not in prompt
