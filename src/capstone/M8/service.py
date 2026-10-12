from .schemas import ReviewRequest, ReviewResponse
from .guardrails import DISCLAIMER, scan_sources, validate_citations, decide_route
from .judges import JudgeInput, run_judges

def review(request: ReviewRequest) -> ReviewResponse:
    candidate = request.candidate
    flags = scan_sources(request.question, request.retrieved_documents)
    flags.extend(validate_citations(candidate, request.source_ids))

    scores, consensus, unanimous = run_judges(JudgeInput(
        question=request.question,
        answer=candidate.answer,
        contexts=request.retrieved_documents,
    ))
    route = decide_route(candidate, flags, unanimous)

    # A disclaimer is attached server-side; it is not trusted to the model.
    return ReviewResponse(
        answer=candidate.answer,
        citations=candidate.citations,
        risk_score=candidate.risk_score,
        final_route=route,
        disclaimer=DISCLAIMER,
        guardrail_flags=flags,
        judge_scores=scores,
        judge_consensus=consensus,
    )
