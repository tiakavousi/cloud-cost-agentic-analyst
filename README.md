# FinOps Agentic Analyst ☁️📉

An autonomous AI Data Science agent designed to ingest, clean, and analyze complex cloud infrastructure billing data. Built with a focus on local privacy and enterprise-grade error recovery.

## 🚀 The Mission
Cloud billing data (AWS, Azure, GCP) is notoriously messy and inconsistent. This project moves beyond standard RAG to provide an **Agentic Loop** that can:
- **Normalize Schemas:** Automatically map inconsistent provider column names to a unified structure (FOCUS-compliant).
- **Detect Anomalies:** Autonomously identify cost spikes (e.g., unexpected S3 or Lambda usage) using Pandas.
- **Self-Correct:** Utilize LangGraph to catch Python execution errors and rewrite code in real-time.
- **Visualize Trends:** Generate analytical plots to forecast future cloud spend.

## 🛠️ Tech Stack
- **Orchestration:** LangGraph (Stateful, Multi-step Agents)
- **Brain:** Llama 3.1 via Ollama (Local & Private)
- **Data Engine:** Pandas / NumPy
- **Backend:** FastAPI & Docker
- **Tracing:** LangSmith (for agent reasoning visibility)

## 🏗️ Architecture
The system uses a **StateGraph** to manage the lifecycle of a query:
1. **Input:** User asks a natural language question about cloud costs.
2. **Analysis:** The agent inspects the CSV headers and data types.
3. **Execution:** The agent writes and executes Python code in a secure REPL.
4. **Correction:** If the code fails, the agent interprets the traceback and self-fixes.
5. **Output:** Returns a clean data summary or a visualization.

## 🚦 Getting Started
1. **Clone the repo:** `git clone ...`
2. **Setup Data:** Run the `generate_data.py` script to create the messy billing CSV.
3. **Spin up Containers:** `docker compose up -d --build`
4. **Query:** Send a message to the chat endpoint to start the analysis.