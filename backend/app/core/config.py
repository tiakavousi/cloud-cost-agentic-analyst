import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Cloud Cost Agentic Analyst API"
    # DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://admin:securepassword123@localhost:5432/vectordb")
    DATASET_PATH: str = os.getenv("DATASET_PATH", "data/messy_cloud_billing.csv")
    # LANGCHAIN_DB_URL: str = os.getenv("LANGCHAIN_DB_URL", "postgresql+psycopg2://admin:securepassword123@localhost:5432/vectordb")
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://192.168.1.214:11434")
    COLLECTION_NAME: str = "health_documents"
    UPLOAD_DIR: str = "uploaded_docs"

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()