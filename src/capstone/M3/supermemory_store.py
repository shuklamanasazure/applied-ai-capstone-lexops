"""Small HTTP wrapper around Supermemory for persistent counterparty memory."""

# Import HTTP client for asynchronous API calls.
import httpx

# Import configuration.
from .config import settings


class SupermemoryStore:
    """Persist and recall memories scoped to a counterparty."""

    def __init__(self) -> None:
        # Store API URL and key once so all operations use the same configuration.
        self.base_url = settings.supermemory_base_url.rstrip("/")
        self.api_key = settings.supermemory_api_key

    def _headers(self) -> dict[str, str]:
        # Return the standard Supermemory bearer authentication header.
        return {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

    async def add_memory(self, counterparty_id: str, content: str, metadata: dict) -> str:
        # Fail early when the external memory service is not configured.
        if not self.api_key:
            raise RuntimeError("SUPERMEMORY_API_KEY is required.")
        # Use containerTags to logically isolate a counterparty's memories.
        body = {
            "content": content,
            "metadata": {**metadata, "counterparty_id": counterparty_id},
            "containerTags": [settings.supermemory_namespace, f"counterparty:{counterparty_id}"],
        }
        # Send the memory to Supermemory.
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(f"{self.base_url}/memories", headers=self._headers(), json=body)
            # Raise a clear exception for API errors.
            response.raise_for_status()
            # Return the created memory/document ID.
            return response.json().get("id", "")

    async def search(self, counterparty_id: str, query: str, top_k: int = 5) -> list[dict]:
        # Fail early when the external memory service is not configured.
        if not self.api_key:
            raise RuntimeError("SUPERMEMORY_API_KEY is required.")
        # Search only the target counterparty's memory container.
        body = {
            "q": query,
            "limit": top_k,
            "containerTags": [settings.supermemory_namespace, f"counterparty:{counterparty_id}"],
        }
        # Execute semantic memory search.
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(f"{self.base_url}/search", headers=self._headers(), json=body)
            # Surface API errors to the FastAPI layer.
            response.raise_for_status()
            # Read the standard result list.
            data = response.json()
        # Normalize Supermemory results to the same shape as Qdrant results.
        results = []
        for item in data.get("results", []):
            chunks = item.get("chunks", [])
            content = "\n".join(chunk.get("content", "") for chunk in chunks)
            results.append({
                "source": "supermemory",
                "score": item.get("score"),
                "content": content,
                "metadata": item.get("metadata", {}),
            })
        return results
