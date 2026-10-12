import time  # Measure overall workflow latency.
from typing import TypedDict  # Define the shared LangGraph state.
from langgraph.graph import StateGraph, END  # Build a typed, explicit workflow graph.
from langfuse import observe  # Create Langfuse observations for each pipeline stage.
from .schemas import ReviewRequest, ReviewResult  # Reuse Pydantic request/result contracts.
from .reliability import parse_large_document, ControlledFailure  # Reuse bounded parsing and failures.
from .tracing import MODEL_NAME, PROMPT_VERSION, review_trace_attributes  # Central trace configuration.


class ReviewState(TypedDict, total=False):
    # Shared state passed between LangGraph nodes; avoid placing full text in Langfuse metadata.
    request: ReviewRequest
    sections: list[str]
    clauses: list[str]
    retrieval_results: list[str]
    risk_score: int
    redline: str
    final_route: str
    human_decision: str
    errors: list[str]
    started_at: float
    latency_ms: int


@observe(name="Extraction", capture_input=False, capture_output=False)
def extraction_node(state: ReviewState) -> dict:
    # Parse the contract into bounded sections rather than sending the whole document to the LLM.
    sections = parse_large_document(state["request"].document_text)
    # Demo clause detection: retain sections with contract-relevant keywords.
    keywords = ("termination", "liability", "indemnity", "renewal", "governing law")
    candidates = [section for section in sections if any(k in section.lower() for k in keywords)]
    # If no keyword is found, do not fabricate clauses; return an empty candidate list.
    return {"sections": sections, "clauses": candidates}


@observe(name="Playbook Retrieval", capture_input=False, capture_output=False)
def retrieval_node(state: ReviewState) -> dict:
    # Replace these IDs with results from your M3 Qdrant dense/sparse search and reranker.
    # Keep IDs/scores in telemetry; avoid logging the retrieved clause text in production.
    results = ["playbook:liability-cap", "playbook:termination"]
    return {"retrieval_results": results}


@observe(name="Risk Calculation", capture_input=False, capture_output=False)
def risk_node(state: ReviewState) -> dict:
    # Demo scoring rule only; replace with your M2/M5 risk calculator and playbook comparison.
    score = min(100, len(state.get("clauses", [])) * 20)
    return {"risk_score": score}


@observe(name="Redline", capture_input=False, capture_output=False)
def redline_node(state: ReviewState) -> dict:
    # A placeholder redline; connect your M5/M6 redline agent here.
    # Never represent a placeholder as a real legal recommendation.
    return {"redline": "DEMO_ONLY: connect the approved redline drafting agent."}


@observe(name="Legal Review Routing", capture_input=False, capture_output=False)
def legal_review_node(state: ReviewState) -> dict:
    # Require human review when risk is 50 or higher; adjust threshold with legal governance.
    score = state.get("risk_score", 100)
    route = "auto_approve" if score < 50 else "human_review"
    # Human decision remains pending until a real reviewer records an explicit decision.
    decision = "pending" if route == "human_review" else "pending"
    return {"final_route": route, "human_decision": decision}


def build_graph():
    # Define the workflow's shared state schema.
    graph = StateGraph(ReviewState)
    # Register one node per review stage for clear trace hierarchy.
    graph.add_node("extraction", extraction_node)
    graph.add_node("retrieval", retrieval_node)
    graph.add_node("risk", risk_node)
    graph.add_node("redline", redline_node)
    graph.add_node("legal_review", legal_review_node)
    # Connect nodes in execution order.
    graph.set_entry_point("extraction")
    graph.add_edge("extraction", "retrieval")
    graph.add_edge("retrieval", "risk")
    graph.add_edge("risk", "redline")
    graph.add_edge("redline", "legal_review")
    graph.add_edge("legal_review", END)
    # Compile into an executable graph; add a checkpointer for resumability in production.
    return graph.compile()


review_graph = build_graph()  # Build once at import time and reuse across API requests.


@observe(name="Review", capture_input=False, capture_output=False)
def run_review(request: ReviewRequest) -> ReviewResult:
    # Start latency measurement before executing any pipeline stage.
    started_at = time.perf_counter()
    # Add safe correlation metadata to the Langfuse trace and all nested observations.
    with review_trace_attributes(request.review_id, request.contract_id, request.counterparty):
        try:
            # Invoke the LangGraph pipeline with the validated request.
            state = review_graph.invoke({"request": request, "started_at": started_at, "errors": []})
            # Calculate end-to-end latency in milliseconds.
            latency_ms = int((time.perf_counter() - started_at) * 1000)
            # Build a validated, explicit response model.
            return ReviewResult(
                review_id=request.review_id,
                contract_id=request.contract_id,
                risk_score=state["risk_score"],
                latency_ms=latency_ms,
                final_route=state["final_route"],
                human_decision=state["human_decision"],
                model=MODEL_NAME,
                prompt_version=PROMPT_VERSION,
                token_usage={},  # Populate from real provider usage when real LLM calls are connected.
                retrieval_results=state.get("retrieval_results", []),
                tool_calls=[],  # Populate with MCP tool names/IDs when MCP tools are invoked.
                errors=[],
            )
        except ControlledFailure as exc:
            # Record only a sanitized error code; never attach contract text or secrets.
            return ReviewResult(
                review_id=request.review_id,
                contract_id=request.contract_id,
                risk_score=100,
                latency_ms=int((time.perf_counter() - started_at) * 1000),
                final_route="human_review",
                human_decision="pending",
                model=MODEL_NAME,
                prompt_version=PROMPT_VERSION,
                errors=[str(exc)],
            )
