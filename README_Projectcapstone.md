The key is to make every milestone produce a reusable component that becomes part of the next milestone.

The architecture should evolve like this:

M1 structured extraction → M2 tool-using agent → M3 memory + vector store → M4 production RAG → M5 deterministic LangGraph workflow → M6 multi-agent + MCP → M7 observability/reliability → M8 evaluation + guardrails + API.

Milestones (map 1:1 to the 8 lab sessions)
Milestone	What the team builds
M1	Extract key clauses (term, termination, liability cap, indemnification, governing law) from raw contract text into a validated Pydantic ContractSummary.
M2	Single agent with tools: clause-risk calculator (deviation from standard terms), renewal-date calendar, and file-writing for summary memos.
M3	Persistent memory of past negotiations per counterparty + a Qdrant index over the firm's clause playbook and past approved redlines.
M4	Production RAG over the playbook and past contracts with hybrid search/reranking; evaluate whether cited clauses are actually grounded in the source playbook.
M5	LangGraph workflow: extract → compare-to-playbook → draft redline → conditional route (standard = auto-approve, non-standard = human-approval interrupt), with checkpointing.
M6	Multi-agent team (Extraction, Playbook RAG, Redline Drafter, Legal Reviewer) with an MCP server exposing a contract repository / e-signature mock API.
M7	LangFuse tracing across the review pipeline; reliability hardening for long-document parsing failures and API timeouts.
M8	Golden eval set of 20 clause-review cases including deliberately non-standard clauses; guardrails force a "not legal advice, human review required" disclaimer and block auto-approval above a risk threshold; FastAPI packaging.


Important: 
Each folder in the project structure, from M1 to M8, corresponds to a specific objective from the list above. Each folder contains Python files that can be executed as an independent application by following the instructions in its respective README.md file. The README also includes sample payloads and corresponding curl commands to validate the application's functionality.
