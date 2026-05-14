from sqlalchemy import create_engine
from langchain_community.chat_models import ChatOllama
from langchain_community.embeddings import OllamaEmbeddings
from app.core.config import settings

# Global engine instance to share connection pooling
engine = create_engine(settings.DATABASE_URL)

def get_db_engine():
    return engine

def get_embeddings():
    return OllamaEmbeddings(
        model="nomic-embed-text",
        base_url=settings.OLLAMA_BASE_URL
    )

def get_llm():
    return ChatOllama(
        model="llama3", 
        temperature=0.3,
        base_url=settings.OLLAMA_BASE_URL
    )