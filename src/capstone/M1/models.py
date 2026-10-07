# Import date so that Pydantic can validate dates automatically.
from datetime import date

# Import BaseModel for creating Pydantic models.
# Field allows us to add descriptions and constraints.
from pydantic import BaseModel, Field


# Represents where an extracted clause came from in the contract.
class SourceReference(BaseModel):

    # Page number is optional because page extraction is not required in M1.
    page: int | None = None

    # Section identifies the contract section when available.
    section: str | None = None

    # Starting character position in the original contract.
    start_character: int | None = None

    # Ending character position in the original contract.
    end_character: int | None = None


# Common information that every extracted clause should contain.
class ClauseBase(BaseModel):

    # Exact wording from the source contract.
    # None means that the clause was not found.
    raw_text: str | None = None

    # Location/provenance information for the extracted clause.
    source_reference: SourceReference | None = None


# Represents the contract term clause.
class TermClause(ClauseBase):

    # Contract start date, when explicitly available.
    start_date: date | None = None

    # Contract end date, when explicitly available.
    end_date: date | None = None

    # Renewal information exactly as understood from the contract.
    renewal: str | None = None


# Represents the termination clause.
class TerminationClause(ClauseBase):

    # Notice period expressed as text.
    # Example: "30 days".
    notice_period: str | None = None

    # Description of termination rights.
    termination_rights: str | None = None


# Represents the liability limitation clause.
class LiabilityCapClause(ClauseBase):

    # Monetary amount when the contract explicitly provides one.
    amount: float | None = None

    # Multiplier when the contract expresses the cap as a multiple.
    # Example: "2x annual fees".
    multiplier: str | None = None

    # Exceptions to the liability cap.
    exceptions: str | None = None


# Represents the indemnification clause.
class IndemnificationClause(ClauseBase):

    # Description of what the indemnifying party covers.
    scope: str | None = None


# Represents the governing-law clause.
class GoverningLawClause(ClauseBase):

    # Jurisdiction specified by the contract.
    jurisdiction: str | None = None


# This is the final M1 output contract.
class ContractSummary(BaseModel):

    # Unique identifier of the contract.
    contract_id: str

    # Name of the other contracting party.
    counterparty: str

    # Extracted term information.
    term: TermClause

    # Extracted termination information.
    termination: TerminationClause

    # Extracted liability-cap information.
    liability_cap: LiabilityCapClause

    # Extracted indemnification information.
    indemnification: IndemnificationClause

    # Extracted governing-law information.
    governing_law: GoverningLawClause


# Input object given to the extraction component.
class ContractReviewRequest(BaseModel):

    # Contract identifier.
    contract_id: str

    # Contract counterparty.
    counterparty: str

    # Raw contract text.
    contract_text: str