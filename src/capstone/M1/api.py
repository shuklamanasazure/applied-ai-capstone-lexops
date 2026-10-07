# Import FastAPI.
from fastapi import FastAPI, HTTPException

# Import input and output models.
from .models import ContractReviewRequest, ContractSummary

# Import our reusable extraction function.
from .extractor import extract_contract


# Create the FastAPI application.
app = FastAPI(
    title="LexOps Contract Clause Extractor",
    version="1.0.0",
)


# Define the contract extraction endpoint.
@app.post(
    "/extract",
    response_model=ContractSummary,
)
def extract(request: ContractReviewRequest) -> ContractSummary:

    # Try the extraction operation.
    try:

        # Call the reusable M1 component.
        return extract_contract(request)

    # Convert validation/extraction errors into HTTP 422.
    except ValueError as exc:

        # Return a meaningful API error.
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        )