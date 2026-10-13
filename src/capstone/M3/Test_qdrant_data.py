from qdrant_client import QdrantClient
from capstone.M3.config import settings

client = QdrantClient(
    url=settings.qdrant_url,
    api_key=settings.qdrant_api_key,
)

collection = settings.qdrant_collection

# Check collection statistics
info = client.get_collection(collection)
print("Collection:", collection)
print("Stored points:", info.points_count)

# Retrieve stored chunks and their payloads
records, next_offset = client.scroll(
    collection_name=collection,
    limit=5,
    with_payload=True,
    with_vectors=False,
)

for record in records:
    payload = record.payload or {}
    print("\n" + "=" * 60)
    print("Point ID:", record.id)
    print("Source file:", payload.get("source_file"))
    print("Chunk number:", payload.get("chunk_number"))
    print("Clause type:", payload.get("clause_type"))
    print("Chunk text:", payload.get("text", ""))