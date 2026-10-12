import re
from .schemas import AgentAnswer

DISCLAIMER = "Not legal advice. Human review required."
RISK_THRESHOLD = 0.60

# Starter patterns only: regex is a useful signal, not a complete injection defense.
INJECTION_PATTERNS = {
    "ignore_previous_instructions": r"ignore\s+(all\s+)?previous\s+instructions",
    "disregard_system_instructions": r"disregard\s+(the\s+)?(system|developer)\s+instructions",
    "reveal_system_prompt": r"reveal\s+(the\s+)?system\s+prompt",
    "override_safety": r"override\s+(all\s+)?safety\s+(rules|guardrails)",
    "bypass_guardrails": r"bypass\s+(the\s+)?(security|guardrails)",
    "developer_mode": r"you\s+are\s+now\s+in\s+developer\s+mode",
}

def scan_text(text: str) -> list[str]:
    findings = []
    for name, pattern in INJECTION_PATTERNS.items():
        if re.search(pattern, text, flags=re.IGNORECASE):
            findings.append(f"injection_detected:{name}")
    return findings

def scan_sources(question: str, documents: list[str]) -> list[str]:
    findings = [f"question:{x}" for x in scan_text(question)]
    for index, document in enumerate(documents):
        findings.extend(f"document_{index}:{x}" for x in scan_text(document))
    return findings

def validate_citations(answer: AgentAnswer, source_ids: list[str]) -> list[str]:
    allowed = set(source_ids)
    invalid = sorted(set(answer.citations) - allowed)
    return [f"invalid_citation:{citation}" for citation in invalid]

def decide_route(answer: AgentAnswer, flags: list[str], unanimous_faithful: bool,
                 risk_threshold: float = RISK_THRESHOLD) -> str:
    # Fail closed: no flags, risk below threshold, low/medium risk label,
    # proposed auto-approval, and all three judges must agree.
    if flags:
        return "human_review"
    if answer.risk_score >= risk_threshold:
        return "human_review"
    if answer.risk_level in ("high", "critical"):
        return "human_review"
    if answer.proposed_route != "auto_approve":
        return "human_review"
    if not unanimous_faithful:
        return "human_review"
    return "auto_approve"
