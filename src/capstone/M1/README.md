- To execute the Program and Test
# cd ~/lexops-project/applied-ai-capstone-lexops
# uv run uvicorn capstone.M1.api:app --reload --port 8001  (Start the application)

To Test the Fast API get call
# curl http://127.0.0.1:8001/M1health

To validate the logic
    1. Created a Json File(request.json) matched with schema written in models.py
    Request.json
    {
      "contract_id": "NW-CR-83921",
      "counterparty": "Vortex Dynamics Inc.",
      "contract_text": "This Agreement shall commence on January 1, 2026 and remain in effect until December 31, 2027. Either party may terminate this Agreement by providing thirty days written notice. The total liability of either party shall not exceed $1,000,000. Vendor shall indemnify Customer against third-party claims. This Agreement shall be governed by the laws of Delaware."
    }

    2. Give a post call with curl command 
    curl -X POST "http://localhost:8001/extract"   -H "Content-Type: application/json"   --data @request.json
    It will give the output as per schema defined in models.py for ContractSummary
