"""Application configuration loaded from environment variables."""

# Import BaseSettings so configuration can come from environment variables or .env.
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Point to the assignment corpus directory.
    corpus_dir: str = "/data/lexops/corpus"
    # Point to the local or cloud Qdrant server.
    qdrant_url: str = "http://localhost:6333"
    # Optional Qdrant API key for Qdrant Cloud.
    qdrant_api_key: str | None = None
    # Keep one collection for all organizational knowledge.
    qdrant_collection: str = "lexops_knowledge"
    # Gemini API key used for embeddings and default LLM.
    gemini_api_key: str | None = None
    # Keep the generation model configurable because free-tier model availability changes.
    gemini_model: str = "gemini-2.5-flash"
    # Use Gemini embedding model for Qdrant vectors.
    gemini_embedding_model: str = "gemini-embedding-001"
    # 768 is a practical assignment-sized embedding dimension.
    embedding_dimension: int = 768
    # Supermemory API key stores persistent counterparty memories.
    supermemory_api_key: str | None = None
    # Keep the Supermemory base URL configurable for API-version changes.
    supermemory_base_url: str = "https://api.supermemory.ai/v3"
    # All counterparty memories live in this logical namespace/tag family.
    supermemory_namespace: str = "lexops"
    # Select Gemini by default; set to claude when an Anthropic key is available.
    llm_provider: str = "gemini"
    # Optional Anthropic API key.
    claude_api_key: str | None = None
    # Configurable Claude model.
    claude_model: str = "claude-haiku-4-5"
    # Limit prompt size to reduce free-tier token usage.
    max_llm_input_chars: int = 12000

    # Read values from a local .env file when it exists.
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


# Create one reusable settings object for the whole application.
settings = Settings()
