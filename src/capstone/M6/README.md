- To execute the Program and Test
# cd ~/lexops-project/applied-ai-capstone-lexops
# uv run uvicorn capstone.M6.main:app  --host 0.0.0.0 --port 8006  > m6.log 2>&1 &  (Start the application in background)

# Save the process ID. 
# echo $! > m6.pid

To Test the Fast API get call
# curl http://127.0.0.1:8006/M6health


To Test the application:
# Submit a contract review using a real fixture ID. 
curl -s -X POST http://127.0.0.1:8006/reviews \ -H "Content-Type: application/json" \ -d '{"contract_id":"NW-K-00000"}'

(.venv) ubuntu@ip-172-31-23-36:~/lexops-project/applied-ai-capstone-lexops$ curl -s -X POST http://127.0.0.1:8006/reviews \tp://127.0.0.1:8006/reviews \
  -H "Content-Type: application/json" \
  -d '{"contract_id":"NW-K-00000"}'
{"contract_id":"NW-K-00000","summary":{"contract_id":"NW-K-00000","counterparty_id":"NW-CP-0110","clauses":[]},"findings":[],"redlines":[],"decision":{"status":"human_review","reasons":["No supported clauses were extracted."]}}
