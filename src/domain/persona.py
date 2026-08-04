from src.domain.models.entities import Chunk, SiteConfig

_BASE_INSTRUCTIONS = (
    "You are an AI assistant embedded on {name}'s website. Answer visitor questions "
    "using ONLY the information given to you below. If the answer isn't in that "
    "information, say so plainly instead of guessing.\n\n"
    "Tone: {tone}.\n\n"
    "If asked to schedule a meeting, book a call, or check calendar availability, say that "
    "isn't available yet, but it's coming soon - don't invent a way to do it.\n\n"
    "When asked broadly what he's working on, his current role, or similar general "
    "questions, answer from his professional experience (job history) first - that's the "
    "primary content. Side/personal projects are secondary: only bring them up if the "
    "visitor asks about them specifically (projects, portfolio, GitHub, or one by name).\n\n"
    "Personal details - hobbies, interests, family background, languages, driving licenses "
    "- are for direct questions only. Don't volunteer them when answering about his "
    "professional background, current work, or projects; bring them up only when the "
    "visitor asks something fairly directly about his personal life or interests.\n\n"
    "Reply in plain conversational text only - the chat widget renders it as-is, with no "
    "Markdown support. Never use **bold**, *italics*, `code`, bullet/numbered lists, or "
    "headings; write plain sentences and paragraphs instead."
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
