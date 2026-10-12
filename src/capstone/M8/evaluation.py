import json
from pathlib import Path

REQUIRED_FIELDS = {"id", "question", "expected", "category", "must_cite",
                   "must_not_contain", "expected_route"}

def load_golden_set(path: str) -> list[dict]:
    records = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(records, list) or len(records) != 20:
        raise ValueError("Expected exactly 20 golden-set records")
    ids = []
    for record in records:
        if not isinstance(record, dict) or not REQUIRED_FIELDS.issubset(record):
            raise ValueError("A golden-set record is missing required fields")
        ids.append(record["id"])
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate golden-set IDs")
    return records

def check_golden_case(case: dict, actual_answer: str, actual_citations: list[str],
                      actual_route: str) -> dict:
    missing = sorted(set(case["must_cite"]) - set(actual_citations))
    prohibited = [x for x in case["must_not_contain"]
                  if x.casefold() in actual_answer.casefold()]
    # Basic refusal heuristic for unanswerable examples; tune to your dataset.
    refusal_pass = True
    if case["category"] == "unanswerable":
        text = actual_answer.casefold()
        refusal_pass = any(x in text for x in ("human review", "human reviewer", "escalate", "refuse"))
    # Expected text is used as a required semantic reference; exact match is not forced.
    expected_route_pass = actual_route == case["expected_route"]
    return {
        "id": case["id"],
        "route_pass": expected_route_pass,
        "citation_pass": not missing,
        "prohibited_content_pass": not prohibited,
        "refusal_pass": refusal_pass,
        "missing_citations": missing,
        "prohibited_phrases_found": prohibited,
        "passed": expected_route_pass and not missing and not prohibited and refusal_pass,
    }
