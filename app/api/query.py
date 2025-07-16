from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query
from loguru import logger

from app.models.schemas import QueryRequest, QueryResponse, ErrorResponse
from app.services.rag_service import rag_service


router = APIRouter(prefix="/query", tags=["query"])


@router.post("/", response_model=QueryResponse)
async def process_query(query_request: QueryRequest):
    """Process a RAG query and return response."""
    try:
        logger.info(f"Received query: {query_request.query[:100]}...")
        
        # Process the query
        response = await rag_service.process_query(query_request)
        
        return response
        
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history")
async def get_query_history(limit: int = Query(default=10, ge=1, le=100)):
    """Get query history."""
    try:
        history = rag_service.get_query_history(limit)
        
        return {
            "history": history,
            "total_queries": len(history)
        }
        
    except Exception as e:
        logger.error(f"Error getting query history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/similar")
async def get_similar_queries(
    query: str = Query(..., description="Query to find similar queries for"),
    limit: int = Query(default=5, ge=1, le=20)
):
    """Get similar queries from history."""
    try:
        similar_queries = await rag_service.get_similar_queries(query, limit)
        
        return {
            "query": query,
            "similar_queries": similar_queries,
            "total_found": len(similar_queries)
        }
        
    except Exception as e:
        logger.error(f"Error getting similar queries: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/history")
async def clear_query_history():
    """Clear query history."""
    try:
        rag_service.clear_history()
        
        return {"message": "Query history cleared successfully"}
        
    except Exception as e:
        logger.error(f"Error clearing query history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_query_stats():
    """Get query service statistics."""
    try:
        stats = rag_service.get_service_stats()
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting query stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/document/{document_id}/summary")
async def get_document_summary(document_id: str):
    """Get summary of a specific document."""
    try:
        summary = await rag_service.get_document_summary(document_id)
        
        if "error" in summary:
            raise HTTPException(status_code=404, detail=summary["error"])
        
        return summary
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document summary: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 