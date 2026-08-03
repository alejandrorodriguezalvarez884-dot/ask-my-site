from assistant.models import SiteConfig
from context.models import Chunk

_BASE_INSTRUCTIONS = (
    "You are an AI assistant embedded on {name}'s website. Answer visitor questions "
    "using ONLY the information given to you below. If the answer isn't in that "
    "information, say so plainly instead of guessing.\n\n"
    "Tone: {tone}."
)


def build_system_prompt(site: SiteConfig, context_chunks: list[Chunk]) -> str:
    """Assembles the system prompt from the site's fixed persona plus whatever context
    chunks were retrieved for the current question."""
    parts = [_BASE_INSTRUCTIONS.format(name=site.name, tone=site.tone)]

    if site.role or site.about:
        parts.append(f"## About {site.name}\nRole: {site.role}\n{site.about}".strip())

    if site.links:
        links = "\n".join(f"- {label}: {url}" for label, url in site.links.items())
        parts.append(f"## Links\n{links}")

    if context_chunks:
        context_text = "\n\n".join(
            f"[{chunk.source}]\n{chunk.text}" for chunk in context_chunks
        )
        parts.append(f"## Relevant context\n{context_text}")

    return "\n\n".join(parts)
