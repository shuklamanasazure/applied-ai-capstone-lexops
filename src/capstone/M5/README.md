- To execute the Program and Test
# cd ~/lexops-project/applied-ai-capstone-lexops
# uv run uvicorn capstone.M5.api:app --reload --port 8004  (Start the application)

To Test the Fast API get call
# curl http://127.0.0.1:8004/M5health

- Submit a Standard review request
curl -X POST http://127.0.0.1:8004/reviews   -H "Content-Type: application/json"   -d '{
    "review_id": "LEXOPS-M5-001",
    "counterparty": "Northwind",
    "contract": "Standard contract wording."
  }'


- Test the human approval path
curl -X POST http://127.0.0.1:8004/reviews \
  -H "Content-Type: application/json" \
  -d '{
    "review_id": "LEXOPS-M5-002",
    "counterparty": "CyberShield",
    "contract": "liability: unlimited"
  }'

- Approve the Review
curl -X POST http://127.0.0.1:8004/reviews/LEXOPS-M5-002/approval \
  -H "Content-Type: application/json" \
  -d '{
    "decision": "approve",
    "reviewer": "lawyer@example.test",
    "comment": "Approved for the assignment test."
  }'


- Retrieve the review state
 curl http://127.0.0.1:8004/reviews/LEXOPS-M5-002
