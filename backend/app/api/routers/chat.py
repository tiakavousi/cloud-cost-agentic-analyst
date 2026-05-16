# app/api/routers/chat.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from langchain_core.messages import HumanMessage
from app.services.agent_service import agent_app

router = APIRouter()

class ChatPayload(BaseModel):
    message: str

@router.post("/chat/")
async def chat_endpoint(payload: ChatPayload):
    # Prepare the initial state required by LangGraph
    inputs = {
        "messages": [HumanMessage(content=payload.message)],
        "dataset_path": "data/messy_cloud_billing.csv",
        # Pass a clean profile of your dataset columns so the intent classifier knows what exists
        "dataset_info": """
        Columns:
        - Usage_Date (string, format YYYY-MM-DD)
        - Cloud_Provider (string, e.g., 'AWS', 'GCP', 'Azure')
        - Service_Name (string, e.g., 'AmazonS3', 'AmazonEC2')
        - Region (string, e.g., 'us-east-1', 'eu-west-2')
        - UnblendedCost (float, numeric cost values)
        - Project_Tag (string)
        """
    }
    
    try:
        # Run the synchronous pipeline graph
        result = agent_app.invoke(inputs)
        
        # Pull processed properties out of the final graph state
        chosen_tool = result.get("chosen_tool", "")
        tool_output = result.get("tool_output", "")
        final_answer = result.get("final_answer", "")
        
        # Check programmatically if the visualization tool was used
        has_chart = chosen_tool == "generate_visualization" and tool_output.startswith("Success:")
        
        # Construct a beautiful, clean JSON object for the frontend
        return {
            "text_summary": final_answer,
            "has_chart": has_chart,
            "chart_url": "http://localhost:8000/static/charts/generated_chart_01.png" if has_chart else None
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent workflow execution failed: {str(e)}")