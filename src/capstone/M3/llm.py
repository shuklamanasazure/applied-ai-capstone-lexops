"""Small provider abstraction for Gemini and optional Claude."""

# Import JSON because extraction is requested as structured JSON.
import json
# Import Any for SDK response typing without coupling the rest of the app to SDK internals.
from typing import Any

# Import Gemini's current unified SDK.
from google import genai
# Import Gemini config types.
from google.genai import types
# Import Anthropic only when Claude is configured.
from anthropic import Anthropic

# Import application settings.
from .config import settings


class LLMService:
    """Provide embeddings and text generation behind one reusable interface."""

    def __init__(self) -> None:
        # Create Gemini client only when a Gemini key exists.
        self.gemini = genai.Client(api_key=settings.gemini_api_key) if settings.gemini_api_key else None
        # Create Claude client only when Claude is selected and a key exists.
        self.claude = Anthropic(api_key=settings.claude_api_key) if settings.claude_api_key else None

    def embed(self, texts: list[str], batch_size: int = 5,) -> list[list[float]]:
        """Create one embedding vector per input text."""
        # Fail early with a useful message instead of a confusing SDK error.
        if not self.gemini:
            raise RuntimeError("GEMINI_API_KEY is required for Qdrant embeddings.")

         all_embeddings: list[list[float]] = []

        for start in range(0, len(texts), batch_size):
            batch = texts[start:start + batch_size]
        
            # Ask Gemini for multiple embeddings in one request to reduce API calls.
            response = self.gemini.models.embed_content(
                model=settings.gemini_embedding_model,
                contents=batch,
                config=types.EmbedContentConfig(output_dimensionality=settings.embedding_dimension),
            )
            # Convert SDK embedding objects into plain Python lists for Qdrant.
            all_embeddings.extend([list(item.values) for item in response.embeddings])
        
        return all_embeddings

    
    def generate(self, prompt: str) -> str:
        """Generate text using the configured provider."""
        # Use Gemini when configured because it is the default low-cost path for this assignment.
        if settings.llm_provider.lower() == "gemini":
            # Ensure a Gemini client exists.
            if not self.gemini:
                raise RuntimeError("GEMINI_API_KEY is required for Gemini generation.")
            # Keep the prompt bounded to avoid consuming excessive free-tier tokens.
            prompt = prompt[: settings.max_llm_input_chars]
            # Generate a concise answer from the configured Gemini model.
            response = self.gemini.models.generate_content(model=settings.gemini_model, contents=prompt)
            # Return plain text so callers do not depend on SDK response classes.
            return response.text or ""

        # Use Claude when explicitly selected.
        if settings.llm_provider.lower() == "claude":
            # Ensure an Anthropic client exists.
            if not self.claude:
                raise RuntimeError("CLAUDE_API_KEY is required when LLM_PROVIDER=claude.")
            # Call Claude with a deliberately small output budget.
            response = self.claude.messages.create(
                model=settings.claude_model,
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt[: settings.max_llm_input_chars]}],
            )
            # Extract text blocks from Claude's response.
            return "".join(block.text for block in response.content if hasattr(block, "text"))

        # Reject invalid providers explicitly.
        raise ValueError("LLM_PROVIDER must be 'gemini' or 'claude'.")

    def extract_memories(self, counterparty_id: str, evidence: str) -> list[dict[str, Any]]:
        """Turn historical negotiation evidence into small durable memory statements."""
        # Give the model a strict output contract to make downstream storage predictable.
        prompt = f"""
You are extracting persistent negotiation memory for counterparty '{counterparty_id}'.
Only extract facts supported by the evidence. Do not invent policy.
Return ONLY valid JSON as an array of objects with keys:
statement, memory_type, evidence.
memory_type must be one of: preference, rejection, acceptance, pattern, escalation.
Keep each statement under 35 words.

Historical evidence:
{evidence}
"""
        # Ask the selected model to perform the extraction.
        raw = self.generate(prompt)
        # Remove common Markdown JSON fences if the model adds them.
        cleaned = raw.replace("```json", "").replace("```", "").strip()
        # Parse the model output into Python data.
        data = json.loads(cleaned)
        # Validate the basic shape before returning it to the API layer.
        if not isinstance(data, list):
            raise ValueError("Memory extraction did not return a JSON array.")
        return data
