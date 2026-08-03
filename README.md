# ask-my-site

A reusable backend for a website AI assistant: a small HTTP API, callable from any frontend,
that answers visitor questions using **two sources of context** —

1. **The site's own persona** (`config/site.yaml`): who it's speaking for, in a few
   sentences you write once.
2. **Whatever documents you drop into `context/`** (Markdown/text): CV content, project
   write-ups, FAQs, anything else the assistant should know about.

**Status: template / draft scaffold.** This repo is meant to be cloned (or its `src/` reused)
per deployment, not run as-is against real traffic yet — see "Open items" below.

## How this becomes *your* assistant

1. `cp config/site.example.yaml config/site.yaml` and fill in your name, role, a short
   "about" blurb, and links. This is the assistant's fixed identity — it doesn't change
   per question.
2. Drop `.md`/`.txt` files into `context/` (subdirectories are fine) — anything you want
   the assistant to be able to answer questions about. Both `config/site.yaml` and
   `context/*` are gitignored, so a deployment's real content never has to live in this repo.
3. `cp .env.example .env`, set `ANTHROPIC_API_KEY`, and set `ALLOWED_ORIGINS` to the
   origin(s) of the site(s) that will call this API from the browser.
4. Run it (see "Running locally" / "Running in Docker" below) and point your frontend's
   chat widget at `POST /chat`.

## How a question gets answered

```
POST /chat  { "message": "...", "history": [...] }
        │
        ▼
BM25Retriever.search(message)   # top-k chunks from context/, ranked by keyword overlap
        │
        ▼
build_system_prompt(site_config, chunks)   # persona + retrieved chunks -> one system prompt
        │
        ▼
ClaudeAssistant.reply(system_prompt, history, message)   # single call to the Anthropic API
        │
        ▼
{ "reply": "..." }
```

Retrieval is lexical (BM25 over keyword overlap, via `rank-bm25`), not embedding-based —
deliberately, the same call made in `custom-llm-finetuning`: for the handful of documents a
personal or small-business site's assistant realistically needs, BM25 needs no model
download and no vector store, and is good enough. `context/models.py`'s `Retriever`
interface exists so an embedding-based implementation can be swapped in later, behind the
same `index()`/`search()` contract, if the context ever grows large enough for that to matter.

## Structure

```
config/site.example.yaml  # Template for config/site.yaml (gitignored) - the assistant's persona
context/.gitkeep          # context/*.md and context/*.txt (gitignored) get indexed at startup
src/
  api/
    settings.py     # Settings: env vars (ANTHROPIC_API_KEY, ALLOWED_ORIGINS, etc.)
    schemas.py      # ChatRequest / ChatResponse (the public HTTP contract)
    routes.py       # GET /health, POST /chat
    app.py          # create_app(): wires settings + site config + retriever + LLM client
  assistant/
    models.py       # SiteConfig, ChatTurn
    config.py       # load_site_config(): reads config/site.yaml
    persona.py      # build_system_prompt(): persona + retrieved chunks -> system prompt
    llm.py          # ClaudeAssistant: the only module that calls the Anthropic API
  context/
    models.py       # Chunk, Retriever interface
    loader.py       # load_context_documents(): reads context/ into Chunks
    retriever.py    # BM25Retriever: the default Retriever implementation
  utils/logging_config.py   # configure_logging()
tests/               # Unit tests - no live network calls (ClaudeAssistant is stubbed
                     # out in test_routes.py; nothing else touches the network)
Dockerfile           # uv-managed image; config/ and context/ are usually bind-mounted
                     # in at runtime instead of baked in (see `make docker-run`)
```

`api`, `assistant`, and `context` are top-level packages directly under `src/`, each with its
own `models.py` for interfaces/schemas and separate files for the actual logic next to it —
same layout convention as `smr-autodata-phase1-ingestion`'s `connectors`/`storage`/`catalog`.

## Running locally (without Docker)

Environment is managed with [uv](https://docs.astral.sh/uv/) — `pyproject.toml` + `uv.lock`
are the source of truth, no `requirements*.txt`. This isn't an installed package (see
`[tool.uv] package = false` in `pyproject.toml`), so `src/` needs to be on `PYTHONPATH` to run
the server directly — `pytest` doesn't need this, it gets `src/` from
`[tool.pytest.ini_options]` instead.

```bash
make install     # uv sync: creates .venv, installs runtime + dev deps from uv.lock
make test        # uv run pytest
make lint         # uv run ruff check .

cp config/site.example.yaml config/site.yaml   # then fill it in
cp .env.example .env                            # then set ANTHROPIC_API_KEY

make dev         # uvicorn with --reload, http://localhost:8000
make run         # same, without --reload (respects $PORT)
```

`GET /health` returns `{"status": "ok"}`. `POST /chat` expects
`{"message": "...", "history": [{"role": "user" | "assistant", "content": "..."}]}` and
returns `{"reply": "..."}`.

## Running in Docker

```bash
make build        # docker build -t ask-my-site .
make docker-run   # builds, then runs with config/ and context/ mounted read-only,
                   # and .env loaded via --env-file
```

`config/` and `context/` are bind-mounted rather than baked into the image so a deployment
can update its persona or documents without a rebuild — the `COPY config/ context/` lines in
the `Dockerfile` just mean the image also works standalone (e.g. `docker run` without the
mounts) with whatever was in the repo at build time.

## Calling it from a website

CORS is enabled via `ALLOWED_ORIGINS` (comma-separated in `.env`), so a browser-side chat
widget on an allowed origin can call `POST /chat` directly:

```js
const response = await fetch("https://your-ask-my-site-deployment/chat", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ message: "What projects have you built?", history: [] }),
});
const { reply } = await response.json();
```

No frontend widget ships in this repo yet — see Open items.

## Open items before this goes beyond a local draft

1. **No deployment story yet.** This repo only covers the backend; where it actually runs
   (Cloud Run, Fly.io, a VPS, etc.) and how `config/site.yaml`/`context/` get onto that host
   are still open.
2. **No frontend widget.** Any site calling this today has to write its own `fetch` call and
   chat UI against `POST /chat` — a small embeddable widget (script tag, like GoatCounter's)
   would make this a genuine drop-in template.
3. **Only `.md`/`.txt` are ingested.** PDFs (a CV export, say) need a text-extraction step
   added to `context/loader.py` before they're usable as context.
4. **No conversation persistence.** `history` is passed in by the caller on every request and
   kept nowhere server-side — fine for a stateless widget, not for anything wanting
   cross-session memory.
5. **No rate limiting or abuse protection** on `POST /chat` — a public endpoint that spends
   API credits per call needs this before it's pointed at real traffic.
6. **Single, non-streaming Claude call.** `ClaudeAssistant.reply()` waits for the full
   response before returning; streaming would improve perceived latency for longer answers.
7. **BM25 retrieval, not embeddings** — see "How a question gets answered" above. Revisit if
   `context/` grows past what keyword overlap can rank well.
