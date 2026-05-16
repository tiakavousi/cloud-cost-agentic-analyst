# app/services/agent_service.py

from typing import TypedDict, Annotated, Sequence
import operator
import json
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage
from langgraph.graph import StateGraph, END
from langchain_community.chat_models import ChatOllama
from app.core.config import settings
from app.analytics.prompts import INTENT_CLASSIFIER_PROMPT, EXECUTIVE_REPORTER_PROMPT
from app.analytics.tools import get_data_profile, calculate_aggregates, generate_visualization

# --- 1. DEFINE THE ADAPTIVE STATE ---
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    dataset_path: str
    dataset_info: str 
    chosen_tool: str
    tool_args: dict
    tool_output: str
    final_answer: str

# --- 2. INITIALIZE THE STATE GRAPH ---
workflow = StateGraph(AgentState)

# --- 3. INITIALIZE SPECIALIZED MODEL WORKERS ---
# Native JSON mode ensures our classification step never returns corrupted string payloads
json_llm = ChatOllama(
    model="llama3", 
    temperature=0, 
    base_url=settings.OLLAMA_BASE_URL,
    format="json"
)

general_llm = ChatOllama(
    model="llama3", 
    temperature=0, 
    base_url=settings.OLLAMA_BASE_URL
)

# --- 4. DEFINE THE SCHEDULING NODES ---

def intent_classifier_node(state: AgentState):
    """Worker 1: Matches human text questions onto precise functional backends."""
    print("⚙️ [Node] Classifying user intent and parsing tools...")
    
    messages = state.get("messages", [])
    user_question = messages[0].content if messages else "Analyze data summary."
    dataset_info = state.get("dataset_info", "No columns profile found.")
    
    formatted_system_prompt = INTENT_CLASSIFIER_PROMPT.format(dataset_info=dataset_info)
    
    response = json_llm.invoke([
        SystemMessage(content=formatted_system_prompt),
        HumanMessage(content=user_question)
    ])
    
    try:
        decision = json.loads(response.content.strip())
        print(f"🎯 [Classifier Decision] Selected Tool: {decision.get('tool')}")
        return {
            "chosen_tool": decision.get("tool", "get_data_profile"),
            "tool_args": decision.get("args", {})
        }
    except Exception as e:
        print(f"❌ [Classifier Error] Failed parsing model JSON: {str(e)}")
        # Fallback safety default
        return {"chosen_tool": "get_data_profile", "tool_args": {"action_type": "summary"}}


def tool_execution_node(state: AgentState):
    """Worker 2: Replaces arbitrary code running with safe, hand-written core functions."""
    print("⚙️ [Node] Executing deterministic data adapters...")
    
    filepath = state.get("dataset_path", "data/messy_cloud_billing.csv")
    tool_name = state.get("chosen_tool")
    args = state.get("tool_args", {})
    
    output_result = ""
    
    # Clean, declarative match-case routing maps
    match tool_name:
        case "get_data_profile":
            output_result = get_data_profile(
                filepath=filepath, 
                action_type=args.get("action_type", "summary")
            )
            
        case "calculate_aggregates":
            output_result = calculate_aggregates(
                filepath=filepath,
                operation=args.get("operation", "sum"),
                target_column=args.get("target_column"),
                group_by_column=args.get("group_by_column")
            )
            
        case "generate_visualization":
            res = generate_visualization(
                filepath=filepath,
                chart_type=args.get("chart_type", "bar"),
                x_col=args.get("x_col"),
                y_col=args.get("y_col")
            )
            if res["success"]:
                output_result = f"Success: Chart saved and stored locally as {res['filename']}"
            else:
                output_result = f"Visualization Error: {res['error']}"
                
        case _:
            output_result = f"Routing Error: Unknown or missing service capability function '{tool_name}'"

    print("✅ [Tool execution completed successfully]")
    return {"tool_output": output_result}


def executive_reporter_node(state: AgentState):
    """Worker 3: Converts computational matrix strings back into clean business answers."""
    print("⚙️ [Node] Formatting corporate analyst insights...")
    
    messages = state.get("messages", [])
    user_question = messages[0].content if messages else "Analyze data."
    tool_output = state.get("tool_output", "")
    
    formatted_reporter_prompt = EXECUTIVE_REPORTER_PROMPT.format(
        user_question=user_question,
        tool_output=tool_output
    )
    
    response = general_llm.invoke([SystemMessage(content=formatted_reporter_prompt)])
    return {"final_answer": response.content}

# --- 5. COMPILE THE STEP FLOW PIPELINE ---

workflow.add_node("classifier", intent_classifier_node)
workflow.add_node("executor", tool_execution_node)
workflow.add_node("reporter", executive_reporter_node)

workflow.set_entry_point("classifier")

# Simple, predictable sequential lines—no fragile loop conditions or infinite recursion crashes!
workflow.add_edge("classifier", "executor")
workflow.add_edge("executor", "reporter")
workflow.add_edge("reporter", END)

agent_app = workflow.compile()