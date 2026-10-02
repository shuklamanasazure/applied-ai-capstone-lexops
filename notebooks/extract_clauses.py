import os, json, time
from pathlib import Path
from dotenv import load_dotenv
from enum import Enum
from typing import Callable

from pydantic import BaseModel, Field, ValidationError
from litellm import completion


# ---------------------------------------------------------
# 1. Define the setup for LLM agnostic
# ---------------------------------------------------------
def main():
    env_path = Path.cwd() / ".env"
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
    else:
        print(f"No .env file found at {env_path}. Copy .env.template to .env and add your API key.")
        print("If you already set the key in your shell, this cell will still proceed.")

    required_keys = ["DATAGEN_GEMINI_API_KEY"]
    missing = [k for k in required_keys if not os.getenv(k)]
    if missing:
        print(f"Missing required keys: {missing}. Add them to your .env file before continuing.")
    else:
        print("Environment OK — required keys found.")


    # ---------------------------------------------------------
    # 2. Validate a record in the input file from data folder
    # ---------------------------------------------------------

    with open("data/lexops/intake/records.jsonl") as f:
        records = json.load(f)
    print(f"Loaded {len(records)} sample intake/records records.")
    print(records[0])


# ---------------------------------------------------------
# 1. Define the allowed clause types
# ---------------------------------------------------------

class ClauseType(str, Enum):
    TERM = "term"
    TERMINATION = "termination"
    LIABILITY_CAP = "liability_cap"
    INDEMNIFICATION = "indemnification"
    GOVERNING_LAW = "governing_law"


# ---------------------------------------------------------
# 2. Define the structure of one extracted clause
# ---------------------------------------------------------

class ExtractedClause(BaseModel):
    present: bool = False
    text: str | None = None
    summary: str | None = None
    deviation: str | None = None
    requires_human_review: bool = False


# ---------------------------------------------------------
# 3. Define the complete LLM response
# ---------------------------------------------------------

class KeyClauses(BaseModel):
    term: ExtractedClause = Field(default_factory=ExtractedClause)
    termination: ExtractedClause = Field(default_factory=ExtractedClause)
    liability_cap: ExtractedClause = Field(default_factory=ExtractedClause)
    indemnification: ExtractedClause = Field(default_factory=ExtractedClause)
    governing_law: ExtractedClause = Field(default_factory=ExtractedClause)


# ---------------------------------------------------------
# 4. LLM extraction function
# ---------------------------------------------------------

def extract_key_clauses(
    record: dict,
    generate_text: Callable[[str], str],
) -> KeyClauses:

    clause_text = record.get("attached_clause_text", "")

    if not clause_text.strip():
        return KeyClauses()

    prompt = f"""
You are a contract clause extraction assistant.

Extract ONLY the following five key clauses from the
provided contract text:

1. Term
2. Termination
3. Liability Cap
4. Indemnification
5. Governing Law

Rules:

- Extract the actual contractual language when available.
- Do not invent information.
- If a clause is not present, set present=false.
- Provide a short summary when the clause is present.
- Identify any obvious deviation or unusual provision.
- Set requires_human_review=true when the clause appears
  unusual, ambiguous, risky, or requires legal judgment.
- Return only the requested structured output.

The response must be valid JSON matching this schema:

{json.dumps(KeyClauses.model_json_schema())}

Contract text:

{clause_text}
"""

    response_text = generate_text(prompt)
    return KeyClauses.model_validate_json(response_text)


# ---------------------------------------------------------
# 5. Process the complete JSONL file
# ---------------------------------------------------------

def process_records(
    generate_text: Callable[[str], str],
    input_file: str = "records.jsonl",
    output_file: str = "extracted_clauses.jsonl",
):
    input_path = Path(input_file)
    output_path = Path(output_file)

    with input_path.open("r", encoding="utf-8") as infile, \
         output_path.open("w", encoding="utf-8") as outfile:

        for line_number, line in enumerate(infile, start=1):

            if not line.strip():
                continue

            try:
                # Read one JSON record
                record = json.loads(line)

                # Extract clauses using the LLM
                clauses = extract_key_clauses(
                    record=record,
                    generate_text=generate_text,
                )

                # Create output record
                result = {
                    "request_id": record.get("request_id"),
                    "record_id": record.get("record_id"),
                    "counterparty_name": record.get(
                        "counterparty_name"
                    ),
                    "key_clauses": clauses.model_dump(),
                }

                # Write one JSON object per line
                outfile.write(
                    json.dumps(result, ensure_ascii=False)
                    + "\n"
                )

                print(
                    f"Processed record {line_number}: "
                    f"{record.get('record_id')}"
                )

            except Exception as exc:
                print(
                    f"Error processing line {line_number}: {exc}"
                )


# --------------------------------------------------------- 
# 7. Application entry point 
# ---------------------------------------------------------
if __name__ == "__main__":
    main()
    # Use the LLM to process the records
    # process_records(
    #     generate_text=lambda prompt: completion(
    #         prompt=prompt,
    #         model="gemini-1.5",
    #         temperature=0.0,
    #         max_tokens=1000,
    #     ),
    #     input_file="data/lexops/intake/records.jsonl",
    #     output_file="data/lexops/output/extracted_clauses.jsonl",
    # )