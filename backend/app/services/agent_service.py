from typing import TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage
import operator
from langgraph.graph import StateGraph, END
from langchain_community.chat_models import ChatOllama
from langchain_experimental.utilities import PythonREPL
from langchain_core.messages import SystemMessage, HumanMessage
from app.core.config import settings

# --- 1. DEFINE THE STATE ---
class AgentState(TypedDict):
    # Tracks the conversation and the LLM's internal reasoning
    # 'operator.add' ensures new messages append to the list rather than overwriting it
    messages: Annotated[Sequence[BaseMessage], operator.add]
    
    # The location of your FinOps data
    dataset_path: str
    
    # A text summary of the CSV (column names, data types) so the LLM knows what to code
    dataset_info: str 
    
    # The Pandas code the LLM writes
    current_code: str
    
    # The terminal output or traceback error from the code execution
    execution_result: str
    
    # The final human-readable answer to send back to the user
    final_answer: str

# --- 2. INITIALIZE THE GRAPH ---
# We instantiate the graph using our custom State
workflow = StateGraph(AgentState)

# --- 3. INITIALIZE THE LLM ---
# Temperature is 0 because we want deterministic, precise code, not creative writing.
llm = ChatOllama(
    model="llama3.1", 
    temperature=0, 
    base_url=settings.OLLAMA_BASE_URL
    )

# --- 4. DEFINE THE NODES (The Workers) ---

def generate_code_node(state: AgentState):
    """Worker 1: Looks at the data schema and writes Python/Pandas code."""
    print("⚙️ [Node] Generating Code...")
    
    # 1. Pull what we need from the state's memory
    messages = state.get("messages", [])
    user_question = messages[0].content if messages else "Analyze the data."
    dataset_path = state.get("dataset_path", "data/messy_cloud_billing.csv")
    dataset_info = state.get("dataset_info", "No info provided.")
    error_feedback = state.get("execution_result", "")

    # 2. The Ruthless System Prompt
    system_prompt = f"""You are an elite, autonomous FinOps Data Engineer. 
                    Your ONLY job is to write syntactically correct Python code using pandas to answer the user's question.

                    DATASET PATH: '{dataset_path}'
                    DATASET COLUMNS & TYPES:
                    {dataset_info}

                    STRICT RULES:
                    1. Import pandas as pd.
                    2. Load the dataset using pd.read_csv('{dataset_path}').
                    3. Print the final answer using `print()`. Do NOT just leave the variable at the end.
                    4. Output ONLY pure Python code. NO conversational text. NO markdown formatting like ```python. 
                    5. If there is a PREVIOUS ERROR listed below, you MUST fix the code to resolve it.

                    PREVIOUS ERROR TO FIX:
                    {error_feedback if error_feedback else "None. This is the first attempt."}
                    """

    # 3. Call Llama 3.1
    prompt_messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_question)
    ]

    response = llm.invoke(prompt_messages)
    
    # 4. Strip rogue formatting (Local models often disobey the "no markdown" rule)
    raw_code = response.content.strip()
    if raw_code.startswith("```python"):
        raw_code = raw_code[9:]
    if raw_code.startswith("```"):
        raw_code = raw_code[3:]
    if raw_code.endswith("```"):
        raw_code = raw_code[:-3]
        
    clean_code = raw_code.strip()
    
    print(f"📝 [Coder output]\n{clean_code}\n")
    
    # 5. Save the code back to the State so the Executor Node can find it
    return {"current_code": clean_code}


# Instantiate the sandbox environment
repl = PythonREPL()

def execute_code_node(state: AgentState):
    """Worker 2: Runs the Python code safely and captures the output or error."""
    print("⚙️ [Node] Executing Code...")
    code = state.get("current_code", "")
    
    if not code:
        return {"execution_result": "Error: No code was generated."}

    # The REPL catches stdout (what prints to the terminal) and errors
    try:
        result = repl.run(code)
        
        # Sometimes the LLM writes valid code but forgets to print the result
        if not result.strip():
            result = "Error: Code executed successfully but printed nothing. You MUST use print() to output the answer."
            
        print(f"✅ [Execution Output]\n{result.strip()}\n")
        return {"execution_result": result.strip()}
        
    except Exception as e:
        # If the code crashes the REPL entirely, we catch the traceback
        error_msg = f"Execution Error: {str(e)}"
        print(f"❌ [Execution Error]\n{error_msg}\n")
        return {"execution_result": error_msg}


def format_response_node(state: AgentState):
    """Worker 3: Takes the raw data output and makes it human-readable."""
    print("⚙️ [Node] Formatting Final Response...")
    
    messages = state.get("messages", [])
    user_question = messages[0].content if messages else "Analyze the data."
    execution_result = state.get("execution_result", "")
    
    # We prompt the LLM one last time to act as the "Reporter"
    prompt = f"""You are a professional FinOps Analyst. 
    The user asked: "{user_question}"
    
    The data analysis script produced this raw output:
    {execution_result}
    
    Formulate a clear, polite, and professional answer for the user based ONLY on this raw output. 
    Do NOT mention Python code, pandas, or the script. Just deliver the business insight.
    """
    
    response = llm.invoke([HumanMessage(content=prompt)])
    return {"final_answer": response.content}


# --- 5. DEFINE THE ROUTING LOGIC ---

def check_for_errors(state: AgentState):
    """The Traffic Cop: Decides if we loop back to fix code, or move to formatting."""
    result = state.get("execution_result", "").lower()
    
    # If the execution result contains error keywords, we route BACK to the Coder
    if "error" in result or "traceback" in result or "exception" in result:
        print("🔄 [Router] Error detected. Looping back to the Coder...")
        return "loop_back"
    
    print("➡️ [Router] Execution successful. Moving to Formatting...")
    return "move_forward"


# --- 6. COMPILE THE GRAPH ---

# Add our workers to the factory floor
workflow.add_node("coder", generate_code_node)
workflow.add_node("executor", execute_code_node)
workflow.add_node("formatter", format_response_node)

# Set the starting point
workflow.set_entry_point("coder")

# Create the standard path from Coder -> Executor
workflow.add_edge("coder", "executor")

# Add the Conditional Edge (The Loop)
workflow.add_conditional_edges(
    "executor",             # The node we are leaving
    check_for_errors,       # The function that decides where to go
    {
        "loop_back": "coder",       # If error, go back to write new code
        "move_forward": "formatter" # If success, go to the final formatting
    }
)

# Finish the workflow
workflow.add_edge("formatter", END)

# Compile the final agentic application
agent_app = workflow.compile()