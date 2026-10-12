"""Judge interface and fail-closed consensus.

Framework-specific calls vary by installed Ragas/DeepEval/TruLens versions and
LLM provider. This module intentionally does not fabricate scores: until real
adapters are configured, the API reports not_evaluated and will not auto-approve.
"""
from dataclasses import dataclass
from .schemas import JudgeResult

@dataclass
class JudgeInput:
    question: str
    answer: str
    contexts: list[str]

class JudgeNotConfigured(RuntimeError):
    pass

class BaseJudge:
    name = "base"
    def evaluate(self, data: JudgeInput) -> JudgeResult:
        raise JudgeNotConfigured(f"{self.name} adapter is not configured")

class RagasJudge(BaseJudge):
    name = "ragas"
    # Implement with your installed Ragas version's Faithfulness metric and LLM.

class DeepEvalJudge(BaseJudge):
    name = "deepeval"
    # Implement with FaithfulnessMetric and a configured evaluation model.

class TruLensJudge(BaseJudge):
    name = "trulens"
    # Instrument retrieval/generation and evaluate groundedness/context relevance.

JUDGES = [RagasJudge(), DeepEvalJudge(), TruLensJudge()]

def run_judges(data: JudgeInput) -> tuple[dict[str, float | None], str, bool]:
    """Run all judges. Missing, failed, or incomplete judge results fail closed."""
    scores: dict[str, float | None] = {}
    results: list[JudgeResult] = []
    for judge in JUDGES:
        try:
            result = judge.evaluate(data)
            if result.judge != judge.name:
                raise ValueError("Judge returned mismatched name")
            scores[judge.name] = result.score
            results.append(result)
        except Exception:
            scores[judge.name] = None
    if len(results) != 3:
        return scores, "not_evaluated", False
    if all(r.faithful and r.score >= 0.80 for r in results):
        return scores, "agree_faithful", True
    return scores, "disagree", False
