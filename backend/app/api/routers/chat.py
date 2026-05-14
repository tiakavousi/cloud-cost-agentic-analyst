from fastapi import APIRouter, Depends
from app.schemas.pydantic import ChatRequest
from app.core.dependencies import get_embeddings, get_llm
from app.services.rag_service import generate_rag_response

# The prefix means we don't need to type /chat in the route below
router = APIRouter(prefix="/chat", tags=["Chat"])

@router.post("/")
async def chat_with_bot(request: ChatRequest, llm = Depends(get_llm), embeddings = Depends(get_embeddings)):
    return await generate_rag_response(request.question, request.session_id, llm, embeddings)