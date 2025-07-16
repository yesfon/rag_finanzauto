from datetime import datetime
from fastapi import APIRouter, HTTPException
from loguru import logger

from app.core.config import settings
from app.models.schemas import HealthCheck
from app.services.vector_store import vector_store
from app.services.embeddings import embedding_service
from app.services.llm_service import llm_service


router = APIRouter(prefix="/health", tags=["health"])


@router.get("/", response_model=HealthCheck)
async def health_check():
    """Health check endpoint."""
    try:
        services = {}
        
        # Check vector store
        vector_health = vector_store.health_check()
        services["vector_store"] = vector_health["status"]
        
        # Check embedding service
        try:
            embedding_model = embedding_service.embedding_model
            services["embedding_service"] = "healthy"
        except Exception:
            services["embedding_service"] = "unhealthy"
        
        # Check LLM service
        try:
            llm_model = llm_service.get_model_name()
            services["llm_service"] = "healthy"
        except Exception:
            services["llm_service"] = "unhealthy"
        
        # Overall status
        overall_status = "healthy" if all(
            status == "healthy" for status in services.values()
        ) else "unhealthy"
        
        return HealthCheck(
            status=overall_status,
            timestamp=datetime.now(),
            version=settings.app_version,
            services=services
        )
        
    except Exception as e:
        logger.error(f"Error in health check: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/detailed")
async def detailed_health_check():
    """Detailed health check with service information."""
    try:
        # Vector store stats
        vector_stats = vector_store.get_collection_stats()
        vector_health = vector_store.health_check()
        
        # Embedding service stats
        embedding_stats = embedding_service.get_service_stats()
        
        # LLM service stats
        llm_stats = llm_service.get_service_stats()
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": settings.app_version,
            "services": {
                "vector_store": {
                    "status": vector_health["status"],
                    "stats": vector_stats
                },
                "embedding_service": {
                    "status": "healthy",
                    "stats": embedding_stats
                },
                "llm_service": {
                    "status": "healthy",
                    "stats": llm_stats
                }
            },
            "configuration": {
                "chunk_size": settings.chunk_size,
                "chunk_overlap": settings.chunk_overlap,
                "max_file_size_mb": settings.max_file_size_mb,
                "top_k_results": settings.top_k_results,
                "similarity_threshold": settings.similarity_threshold
            }
        }
        
    except Exception as e:
        logger.error(f"Error in detailed health check: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 