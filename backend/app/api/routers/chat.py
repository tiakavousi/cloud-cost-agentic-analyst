from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from langchain_core.messages import HumanMessage
from app.services.agent_service import agent_app

router = APIRouter(
    prefix="/chat",
    tags=["Agentic Chat"]
)

# Define the expected request payload
class ChatRequest(BaseModel):
    message: str

@router.post("/")
async def chat_with_agent(request: ChatRequest):
    try:
        print(f"📩 [API] Received message: {request.message}")
        
        # 1. Initialize the state with the user's message
        initial_state = {
            "messages": [HumanMessage(content=request.message)],
            # In a production app, you might dynamically set this path
            "dataset_path": "data/messy_cloud_billing.csv",
            # A hardcoded summary of the data so the LLM knows what to query
            "dataset_info": """
            Columns:
            - Usage_Date (string, dates)
            - Cloud_Provider (string)
            - Service_Name (string)
            - Region (string)
            - UnblendedCost (float)
            - Project_Tag (string)
            """
        }
        
        # 2. Run the LangGraph Agent
        # This will loop through Coder -> Executor -> Formatter
        final_state = agent_app.invoke(initial_state)
        
        # 3. Extract the final formatted answer
        answer = final_state.get("final_answer", "Sorry, I couldn't generate an answer.")
        
        return {"response": answer}
        
    except Exception as e:
        print(f"🚨 [API Error] {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))