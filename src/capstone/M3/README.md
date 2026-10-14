# LexOps M3 — Persistent Negotiation Memory + Qdrant Knowledge

Simple FastAPI implementation for the M3 assignment.

## Architecture

- **Qdrant**: firm playbooks, approved redlines and other organizational knowledge.
- **Supermemory**: evolving counterparty-specific negotiation memories.
- **Gemini**: embeddings + memory extraction/reasoning by default.
- **Claude**: optional generation provider via `LLM_PROVIDER=claude`.
- **FastAPI + Pydantic v2**: API and contracts.
- **uv**: dependency/environment management.

- To execute the Program and Test
# cd ~/lexops-project/applied-ai-capstone-lexops
# uv run uvicorn capstone.M3.main:app --reload --port 8003  (Start the application)
# uv run uvicorn capstone.M3.main:app --reload --port 8003 --log-level debug > /tmp/m3.log 2>&1 & (Start application in background)
To Test the Fast API get call
# curl http://127.0.0.1:8003/health

- To test the ingestion into Qdrant from .md files
curl -X POST http://localhost:8003/m3/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "corpus_dir": "/home/ubuntu/lexops-project/applied-ai-capstone-lexops/data/lexops/corpus",
    "recreate": false
  }'


- To test the negotiation API with raw Json data to store in SuperMemory, As per design, It is counterparty data
curl -X POST http://localhost:8003/m3/negotiations  -H "Content-Type: application/json"  --data @negotiation.json

negotiation.json contains: 
{ "counterparty_id": "acme", "contract_id": "acme-2026", "clause_type": "liability", "request": "5x annual fees", "outcome": "approved 2x annual fees", "rationale": "Firm policy and prior Acme precedent", "source": "Acme Contract 2026" }

- To test the extraction from SuperMemory, LLM will analyze the extracted data
curl -X POST http://localhost:8000/m3/memory/extract \ -H "Content-Type: application/json" \ -d '{ "counterparty_id": "acme", "query": "Acme negotiation preferences accepted rejected terms recurring positions", "top_k": 10 }'


- To extract the memory data from SuperMemory
curl http://localhost:8003/m3/counterparties/acme/memory

- Post query to /m3/search and response is result
curl -X POST http://localhost:8003/m3/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Acme is requesting a liability cap of 5x annual fees. What should we propose?",
    "clause_type": "liability",
    "counterparty_id": "acme",
    "top_k": 2
  }'

curl -X POST http://localhost:8003/m3/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "standard liability cap",
    "clause_type": "liability",
    "top_k": 5
  }'
