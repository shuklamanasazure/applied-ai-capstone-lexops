- To execute the Program and Test
# cd ~/lexops-project/applied-ai-capstone-lexops
# uv run uvicorn capstone.M2.api:app --reload --port 8002  (Start the application)

To Test the Fast API get call
# curl http://127.0.0.1:8002/M2health

- To validate the Logic
    • Give a POST call with curl command, Create request.json for input data
    curl -X POST "http://localhost:8002/review"   -H "Content-Type: application/json"   --data @request.json
