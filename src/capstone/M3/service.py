"""M3 application service orchestrating Qdrant, Supermemory and LLM."""

# Import settings for shared limits/configuration.
from .config import settings
# Import schemas used by service methods.
from .schemas import MemoryExtractResponse, MemoryItem, NegotiationOutcome, SearchResult
# Import persistence and AI components.
from .llm import LLMService
from .qdrant_store import QdrantStore
from .supermemory_store import SupermemoryStore


class M3Service:
    """Keep business logic out of FastAPI route handlers."""

    def __init__(self) -> None:
        # Create one shared LLM service.
        self.llm = LLMService()
        # Create Qdrant storage using the same embedding service.
        self.qdrant = QdrantStore(self.llm)
        # Create Supermemory storage for durable counterparty memory.
        self.memory = SupermemoryStore()

    def ingest(self, corpus_dir: str | None, recreate: bool) -> int:
        # Delegate corpus indexing to QdrantStore.
        return self.qdrant.ingest(corpus_dir=corpus_dir, recreate=recreate)

    async def search(self, query: str, clause_type: str | None, counterparty_id: str | None, top_k: int) -> list[SearchResult]:
        # Search organizational knowledge in Qdrant.
        qdrant_results = self.qdrant.search(query, clause_type, counterparty_id, top_k)
        # Search counterparty-specific behavioral memory only when a counterparty was supplied.
        memory_results = await self.memory.search(counterparty_id, query, top_k) if counterparty_id else []
        # Return both evidence sets to the future negotiation agent.
        return [SearchResult(**item) for item in [*qdrant_results, *memory_results]]

    async def add_negotiation(self, outcome: NegotiationOutcome) -> str:
        # Convert the structured negotiation outcome into a concise durable memory.
        content = (
            f"Contract {outcome.contract_id}; clause={outcome.clause_type}; "
            f"request={outcome.request}; outcome={outcome.outcome}; "
            f"rationale={outcome.rationale or 'not provided'}."
        )
        # Store the raw historical fact first; extraction can later consolidate it.
        return await self.memory.add_memory(
            counterparty_id=outcome.counterparty_id,
            content=content,
            metadata={
                "contract_id": outcome.contract_id,
                "clause_type": outcome.clause_type,
                "source": outcome.source or "api",
                "memory_type": "negotiation_outcome",
            },
        )

    async def get_memory(self, counterparty_id: str, query: str = "negotiation preferences accepted rejected recurring positions", top_k: int = 10) -> list[SearchResult]:
        # Recall the counterparty's persistent memories.
        results = await self.memory.search(counterparty_id, query, top_k)
        # Convert raw dictionaries into validated response objects.
        return [SearchResult(**item) for item in results]

    async def extract_memory(self, counterparty_id: str, query: str, top_k: int) -> MemoryExtractResponse:
        # Retrieve historical negotiation evidence from Supermemory.
        evidence_results = await self.memory.search(counterparty_id, query, top_k)
        # Join only the content needed by the extraction model.
        evidence = "\n\n".join(item["content"] for item in evidence_results)
        # Protect the free-tier model from an unnecessarily large prompt.
        evidence = evidence[: settings.max_llm_input_chars]
        # Ask the LLM to transform episodic facts into semantic/procedural-style memory statements.
        extracted = self.llm.extract_memories(counterparty_id, evidence)
        # Validate every extracted memory using Pydantic v2.
        memories = [MemoryItem(**item) for item in extracted]
        # Store each durable statement back in Supermemory so future searches find it directly.
        stored_ids = []
        for memory in memories:
            memory_id = await self.memory.add_memory(
                counterparty_id=counterparty_id,
                content=memory.statement,
                metadata={
                    "memory_type": memory.memory_type,
                    "evidence": memory.evidence,
                    "source": "memory_extraction",
                },
            )
            stored_ids.append(memory_id)
        # Return the structured extraction result.
        return MemoryExtractResponse(counterparty_id=counterparty_id, memories=memories, stored_ids=stored_ids)
