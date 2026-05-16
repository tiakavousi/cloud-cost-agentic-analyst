from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.routers import chat

app = FastAPI(title=settings.PROJECT_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"], # Allows the Next.js frontend
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"], 
)

# --- ENDPOINTS ---
app.include_router(chat.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to the cloud-cost-agentic-analyst Backend"}

