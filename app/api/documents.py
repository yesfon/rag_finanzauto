import os
import uuid
from datetime import datetime
from typing import List, Optional
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from loguru import logger

from app.core.config import settings
from app.models.schemas import (
    DocumentUploadResponse, DocumentProcessingStatus, DocumentMetadata,
    DocumentStatus, ErrorResponse
)
from app.services.document_processor import document_processor
from app.services.embeddings import embedding_service
from app.services.vector_store import vector_store


router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """Upload and process a document."""
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        # Generate document ID
        document_id = str(uuid.uuid4())
        
        # Create upload directory if it doesn't exist
        upload_dir = Path(settings.chroma_persist_directory).parent / "uploads"
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Save uploaded file
        file_path = upload_dir / f"{document_id}_{file.filename}"
        
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Create metadata
        metadata = DocumentMetadata(
            filename=file.filename,
            file_size=len(content),
            content_type=file.content_type or "application/octet-stream",
            upload_timestamp=datetime.now()
        )
        
        # Validate file
        await document_processor.validate_file(str(file_path), file.filename)
        
        # Process document in background
        background_tasks.add_task(
            process_document_background,
            str(file_path),
            document_id,
            metadata
        )
        
        logger.info(f"Document uploaded: {file.filename} (ID: {document_id})")
        
        return DocumentUploadResponse(
            document_id=document_id,
            filename=file.filename,
            status=DocumentStatus.PENDING,
            message="Document uploaded successfully. Processing started.",
            metadata=metadata
        )
        
    except Exception as e:
        logger.error(f"Error uploading document: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


async def process_document_background(
    file_path: str,
    document_id: str,
    metadata: DocumentMetadata
):
    """Background task to process document."""
    try:
        # Process document into chunks
        chunks = await document_processor.process_document(
            file_path, document_id, metadata
        )
        
        # Generate embeddings for chunk contents
        chunk_contents = [chunk.content for chunk in chunks]
        embeddings = await embedding_service.generate_embeddings(chunk_contents)
        
        # Assign embeddings back to chunks
        for i, chunk in enumerate(chunks):
            chunk.embedding = embeddings[i]
            
        # Store in vector database
        await vector_store.add_chunks(chunks)
        
        # Update metadata
        metadata.processing_timestamp = datetime.now()
        metadata.chunk_count = len(chunks)
        
        # Clean up uploaded file
        if os.path.exists(file_path):
            os.remove(file_path)
        
        logger.info(f"Document processing completed: {document_id}")
        
    except Exception as e:
        logger.error(f"Error processing document {document_id}: {str(e)}")
        # Update processing status to failed
        if document_id in document_processor.processing_status:
            document_processor.processing_status[document_id].status = DocumentStatus.FAILED
            document_processor.processing_status[document_id].error_details = str(e)


@router.get("/status/{document_id}", response_model=DocumentProcessingStatus)
async def get_document_status(document_id: str):
    """Get document processing status."""
    try:
        status = document_processor.get_processing_status(document_id)
        
        if not status:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return status
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{document_id}/chunks")
async def get_document_chunks(document_id: str):
    """Get all chunks for a document."""
    try:
        chunks = await vector_store.get_document_chunks(document_id)
        
        if not chunks:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return {
            "document_id": document_id,
            "chunks": chunks,
            "total_chunks": len(chunks)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document chunks: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{document_id}")
async def delete_document(document_id: str):
    """Delete a document and all its chunks."""
    try:
        # Delete from vector store
        success = await vector_store.delete_document_chunks(document_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Clean up processing status
        document_processor.cleanup_processing_status(document_id)
        
        return {"message": f"Document {document_id} deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
async def list_documents():
    """List all documents with their statistics."""
    try:
        # Get vector store statistics
        stats = vector_store.get_collection_stats()
        
        return {
            "total_documents": stats.get("total_chunks", 0),
            "collection_stats": stats
        }
        
    except Exception as e:
        logger.error(f"Error listing documents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list-unique")
async def list_unique_documents():
    """List unique documents with their metadata."""
    try:
        # Get unique document IDs from vector store
        unique_docs = await vector_store.get_unique_document_ids()
        
        return {
            "documents": unique_docs,
            "total_unique_documents": len(unique_docs)
        }
        
    except Exception as e:
        logger.error(f"Error listing unique documents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reset")
async def reset_documents():
    """Reset all documents (delete everything)."""
    try:
        # Reset vector store
        await vector_store.reset_collection()
        
        # Clear processing status
        document_processor.processing_status.clear()
        
        return {"message": "All documents reset successfully"}
        
    except Exception as e:
        logger.error(f"Error resetting documents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/force-cleanup")
async def force_cleanup_documents():
    """Force cleanup of all documents and recreate collection."""
    try:
        # Force cleanup using vector store
        success = vector_store.force_cleanup()
        
        if success:
            # Clear processing status
            document_processor.processing_status.clear()
            
            return {"message": "Force cleanup completed successfully"}
        else:
            raise HTTPException(status_code=500, detail="Force cleanup failed")
        
    except Exception as e:
        logger.error(f"Error in force cleanup: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 