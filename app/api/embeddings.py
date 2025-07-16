from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from loguru import logger

from app.services.embeddings import embedding_service

router = APIRouter(prefix="/embeddings", tags=["embeddings"])

class EmbeddingRequest(BaseModel):
    text: str

class EmbeddingResponse(BaseModel):
    embedding: list[float]

@router.post("/generate", response_model=EmbeddingResponse)
async def generate_embedding(request: EmbeddingRequest):
    """Generate embedding for a given text."""
    try:
        if not request.text:
            raise HTTPException(status_code=400, detail="Text cannot be empty.")
            
        logger.info(f"Generating embedding for text: {request.text[:50]}...")
        
        # Usamos el mismo servicio de embeddings para consistencia
        embedding = await embedding_service.generate_query_embedding(request.text)
        
        return EmbeddingResponse(embedding=embedding)
        
    except Exception as e:
        logger.error(f"Error generating embedding: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 