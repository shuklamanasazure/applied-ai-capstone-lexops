# Import os so that we can read environment variables.
import os
from dotenv import load_dotenv
# Import ContractReviewRequest and ContractSummary.
from .models import ContractReviewRequest, ContractSummary

# Import the extraction instructions.
from .prompts import EXTRACTION_PROMPT

# Import provenance validation.
from .validation import validate_provenance

# Import the Gemini LangChain integration.
from langchain_google_genai import ChatGoogleGenerativeAI

# Load environment variables from .env file.
load_dotenv()

# Read configuration from environment variables.
api_key = os.getenv("DATAGEN_GEMINI_API_KEY")
model = os.getenv("DATAGEN_GEMINI_MODEL")

# Validate required configuration.
if not api_key:
    raise ValueError("DATAGEN_GEMINI_API_KEY is not set in the .env file.")

if not model:
    raise ValueError("DATAGEN_GEMINI_MODEL is not set in the .env file.")


# Create the LLM only once.
# This avoids creating a new model object for every contract.
llm = ChatGoogleGenerativeAI(

    # Read the Gemini model name from the environment.
    # model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
     # Read the Gemini model name from DATAGEN_GEMINI_MODEL.
    model=model,

    # Read the API key from the environment.
    # google_api_key=os.getenv("GEMINI_API_KEY"),
    # Read the Gemini API key from DATAGEN_GEMINI_API_KEY.
    google_api_key=api_key,

    # Keep temperature low because extraction should be deterministic.
    temperature=0,
)


# Tell LangChain that we expect a Pydantic object.
structured_llm = llm.with_structured_output(ContractSummary)


# Main reusable extraction function.
def extract_contract(
    request: ContractReviewRequest,
) -> ContractSummary:

    # Build the exact information that the model needs.
    # We deliberately do not pass arbitrary application state.
    contract_input = f"""
Contract ID:
{request.contract_id}

Counterparty:
{request.counterparty}

Contract Text:
{request.contract_text}
"""

    # Send the extraction request to the structured-output model.
    result = structured_llm.invoke(

        # System instructions define extraction rules.
        [
            ("system", EXTRACTION_PROMPT),

            # User message contains only the required contract data.
            ("human", contract_input),
        ]
    )

    # Explicitly validate that the source text exists.
    validate_provenance(
        result,
        request.contract_text,
    )


    # Pydantic/LangChain returns a ContractSummary.
    return result