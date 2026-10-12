import os
from fastapi import FastAPI, HTTPException
from pydantic import ValidationError
from .schemas import ReviewRequest, ReviewResponse, AgentAnswer
from .guardrails import scan_sources, DISCLAIMER, RISK_THRESHOLD
from .service import review as run_review
from .evaluation import load_golden_set, check_golden_case

app = FastAPI(title="LexOps M8 Guardrails and Evaluation", version="1.0.0")
GOLDEN_PATH = os.getenv("LEXOPS_GOLDEN_SET", "data/lexops/eval/golden_set.json")

@app.get("/health")
def health():
    return {"status": "ok", "module": "M8"}

@app.get("/policy")
def policy():
    return {"risk_threshold": RISK_THRESHOLD,
            "require_unanimous_judges": True,
            "disclaimer": DISCLAIMER,
            "judge_mode": "fail_closed_until_adapters_configured"}

@app.post("/guardrails/scan")
def scan(payload: dict):
    question = payload.get("question", "")
    documents = payload.get("retrieved_documents", [])
    if not isinstance(question, str) or not isinstance(documents, list) or not all(isinstance(x, str) for x in documents):
        raise HTTPException(status_code=422, detail="question must be text and retrieved_documents must be a list of strings")
    findings = scan_sources(question, documents)
    return {"safe_to_process": not findings, "findings": findings}

@app.post("/validate")
def validate(payload: dict):
    try:
        answer = AgentAnswer.model_validate(payload)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=exc.errors())
    return {"valid": True, "risk_score": answer.risk_score, "proposed_route": answer.proposed_route}

@app.post("/review", response_model=ReviewResponse)
def review(payload: ReviewRequest):
    # In a real deployment, this endpoint receives candidate output from M1-M7.
    # The harness never treats an unconfigured judge as a passing judge.
    return run_review(payload)

@app.get("/golden-set")
def golden_set():
    try:
        cases = load_golden_set(GOLDEN_PATH)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Golden set not found: {GOLDEN_PATH}")
    except (ValueError, KeyError) as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    return {"count": len(cases), "cases": cases}

@app.post("/evaluate/case")
def evaluate_case(payload: dict):
    case_id = payload.get("id")
    answer = payload.get("answer")
    citations = payload.get("citations", [])
    route = payload.get("route")
    if not isinstance(answer, str) or not isinstance(citations, list) or not isinstance(route, str):
        raise HTTPException(status_code=422, detail="answer, citations list, and route are required")
    try:
        cases = load_golden_set(GOLDEN_PATH)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Cannot load golden set: {exc}")
    case = next((x for x in cases if x["id"] == case_id), None)
    if case is None:
        raise HTTPException(status_code=404, detail=f"Unknown golden case ID: {case_id}")
    return check_golden_case(case, answer, citations, route)
