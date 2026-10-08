# LexOps M3 — Persistent Negotiation Memory + Qdrant Knowledge

Simple FastAPI implementation for the M3 assignment.

## Architecture

- **Qdrant**: firm playbooks, approved redlines and other organizational knowledge.
- **Supermemory**: evolving counterparty-specific negotiation memories.
- **Gemini**: embeddings + memory extraction/reasoning by default.
- **Claude**: optional generation provider via `LLM_PROVIDER=claude`.
- **FastAPI + Pydantic v2**: API and contracts.
- **uv**: dependency/environment management.

## Setup

```bash
uv venv
source .venv/bin/activate
uv sync
cp .env.example .env
```

Start local Qdrant:

```bash
docker run -p 6333:6333 qdrant/qdrant
```

Set `.env`:

```env
CORPUS_DIR=/data/lexops/corpus
QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION=lexops_knowledge
GEMINI_API_KEY=your_key
GEMINI_MODEL=gemini-2.5-flash
GEMINI_EMBEDDING_MODEL=gemini-embedding-001
SUPERMEMORY_API_KEY=your_key
LLM_PROVIDER=gemini
CLAUDE_API_KEY=
CLAUDE_MODEL=claude-haiku-4-5
```

Run:

```bash
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## M3 endpoints

```text
POST /m3/ingest
POST /m3/search
GET  /m3/counterparties/{counterparty_id}/memory
POST /m3/negotiations
POST /m3/memory/extract
```

## Demonstration

1. `POST /m3/ingest`
2. Add two or three Acme outcomes with `POST /m3/negotiations`.
3. `POST /m3/memory/extract` for `acme`.
4. `GET /m3/counterparties/acme/memory`.
5. `POST /m3/search` with the 5x liability-cap question.

The final agent can combine the Qdrant result and Supermemory result:

```text
Firm standard: 2x annual fees
Approved precedent: 2x–3x for similar enterprise customers
Acme history: previously accepted 2x
Current request: 5x
Recommendation: counter at 2x; escalate above 3x
```
