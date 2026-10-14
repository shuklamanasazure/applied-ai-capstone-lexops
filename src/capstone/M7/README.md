To start the application
    uv run uvicorn capstone.M7.api:app  --host 0.0.0.0 --port 8007  > m7.log 2>&1 &
Start the application with env file: uv run --env-file .env uvicorn capstone.M7.api:app  --host 0.0.0.0 --port 8007

ubuntu@ip-172-31-23-36:~$ curl http://127.0.0.1:8007/health
{"status":"ok"}

Step 7 — Run the tests
The project includes tests for the main reliability scenarios.
# Run all tests.
uv run pytest -q
# Run only reliability tests.
uv run pytest tests/test_reliability.py -v
# Run API tests.
uv run pytest tests/test_api.py -v
Expected test coverage:
Test	Expected behavior
Transient timeout	Retry and succeed
Repeated timeout	Stop at retry limit
Long document	Produce bounded sections
Empty document	Raise controlled failure
Invalid Pydantic output	Fail closed
Health endpoint	Return HTTP 200
Review endpoint	Return a validated review response
