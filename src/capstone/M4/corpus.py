"""Read corpus files and split them into traceable, overlapping chunks."""

import hashlib  # Create repeatable IDs from source locations and text.
import re  # Normalize headings and whitespace.
from pathlib import Path  # Traverse local corpus files.
from dataclasses import dataclass  # Keep indexed chunk records lightweight.


SUPPORTED_SUFFIXES = {".txt", ".md", ".json", ".jsonl", ".csv"}  # Extend for PDFs/DOCX when needed.


@dataclass
class Chunk:
    """One searchable source passage with provenance."""

    chunk_id: str  # Stable identifier.
    document: str  # Relative path to the source file.
    section: str  # Heading if available, otherwise a fallback label.
    text: str  # Exact passage content.
    authority_rank: int  # Source hierarchy rank.


def authority_for(path: Path) -> int:
    """Assign source authority using conservative filename/path heuristics."""

    name = str(path).lower()  # Normalize path for simple matching.
    if "playbook" in name and any(word in name for word in ("approved", "current", "master")):
        return 1  # Current approved playbook is the highest authority.
    if "playbook" in name:
        return 1  # Treat playbook files as primary until metadata is available.
    if any(word in name for word in ("redline", "red-lined", "negotiation")):
        return 2  # Approved historical redlines come second.
    if "current_contract" in name or "current-contract" in name:
        return 3  # Current contract comes third.
    return 4  # Other contracts are lower authority than the playbook.


def read_text(path: Path) -> str:
    """Decode common text formats; structured files are searchable as text."""

    try:
        return path.read_text(encoding="utf-8")  # Prefer UTF-8 for portability.
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="replace")  # Preserve usable text on imperfect data.


def split_chunks(text: str, chunk_chars: int = 900, overlap: int = 120) -> list[tuple[str, str]]:
    """Split text by headings and character windows while retaining section labels."""

    chunks = []  # Accumulate (section, text) pairs.
    section = "Unlabelled section"  # Fallback when no heading exists.
    cleaned = re.sub(r"\r\n?", "\n", text)  # Normalize line endings.
    lines = cleaned.splitlines()  # Keep headings detectable.
    current = []  # Lines belonging to the current section.

    def flush() -> None:
        """Emit overlapping text windows for the current section."""
        body = "\n".join(current).strip()  # Combine current section lines.
        if not body:
            return  # Skip empty sections.
        start = 0  # Start of the next text window.
        while start < len(body):
            part = body[start:start + chunk_chars].strip()  # Create bounded chunk.
            if part:
                chunks.append((section, part))  # Keep source heading with passage.
            if start + chunk_chars >= len(body):
                break  # Stop after final window.
            start += max(1, chunk_chars - overlap)  # Overlap windows to avoid boundary loss.

    for line in lines:
        candidate = line.strip()  # Normalize candidate heading.
        if candidate.startswith("#") or (len(candidate) < 100 and candidate.endswith(":")):
            flush()  # Finish previous section before switching headings.
            current.clear()  # Reset the section buffer.
            section = candidate.lstrip("# ").rstrip(":").strip() or "Unlabelled section"  # Save heading.
        else:
            current.append(line)  # Add body line to active section.
    flush()  # Emit final section.
    return chunks  # Return all source passages.


def load_corpus(corpus_dir: Path, min_chunk_chars: int = 40) -> list[Chunk]:
    """Load all supported files recursively and create source-addressable chunks."""

    if not corpus_dir.exists():
        raise FileNotFoundError(f"Corpus directory does not exist: {corpus_dir}")  # Fail clearly on bad path.
    output = []  # Collect indexed chunks.
    for path in sorted(corpus_dir.rglob("*")):  # Deterministic file ordering makes tests repeatable.
        if not path.is_file() or path.suffix.lower() not in SUPPORTED_SUFFIXES:
            continue  # Ignore unsupported formats and directories.
        text = read_text(path).strip()  # Read source file.
        if not text:
            continue  # Ignore empty files.
        for index, (section, part) in enumerate(split_chunks(text)):
            if len(part) < min_chunk_chars:
                continue  # Remove tiny chunks that are unlikely to be useful.
            relative = str(path.relative_to(corpus_dir))  # Keep portable provenance.
            digest = hashlib.sha1(f"{relative}:{section}:{index}:{part}".encode()).hexdigest()[:16]  # Stable ID.
            output.append(Chunk(digest, relative, section, part, authority_for(path)))  # Save traceable chunk.
    if not output:
        raise ValueError(f"No supported text chunks found under {corpus_dir}")  # Avoid silently serving empty index.
    return output  # Return indexed corpus.
