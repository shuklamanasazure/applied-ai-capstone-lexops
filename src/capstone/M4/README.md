- To execute the Program and Test
# cd ~/lexops-project/applied-ai-capstone-lexops
# uv run uvicorn capstone.M4.main:app --reload --port 8004  (Start the application)
# uv run uvicorn capstone.M3.main:app --reload --port 8003 --log-level debug > /tmp/m3.log 2>&1 & (Start application in background)

curl http://127.0.0.1:8004/health

curl -X POST "http://localhost:8004/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "The supplier limits liability to 0.5x annual fees. What is the approved liability cap and fallback?",
    "top_k": 5,
    "mode": "hybrid_rerank"
  }'

Stage 1 — Dense baseline
Set "mode": "dense" to measure semantic retrieval alone.
Copy mode
Stage 2–3 — Hybrid + RRF
Set "mode": "hybrid" to combine semantic and keyword rankings.
Copy mode
Stage 4 — Hybrid + reranking
Set "mode": "hybrid_rerank" to rerank the fused candidates.
