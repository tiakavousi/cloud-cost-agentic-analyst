from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from app.core.dependencies import get_db_engine, get_embeddings
from app.services.doc_service import process_and_store_document

router = APIRouter(tags=["Documents & System"])

@router.get("/health/db")
def check_db_health(engine = Depends(get_db_engine)):
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
            return {"status": "Database is connected and healthy!"}
    except OperationalError:
        raise HTTPException(status_code=500, detail="Database connection failed.")

@router.post("/upload-pdf/")
async def upload_and_extract_pdf(file: UploadFile = File(...), embeddings = Depends(get_embeddings)):
    return await process_and_store_document(file, embeddings)