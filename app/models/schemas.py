from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class DocumentType(str, Enum):
    """Supported document types."""
    PDF = "pdf"
    TXT = "txt"
    MD = "md"
    DOCX = "docx"


class DocumentStatus(str, Enum):
    """Document processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class DocumentMetadata(BaseModel):
    """Document metadata schema."""
    filename: str
    file_size: int
    content_type: str
    upload_timestamp: datetime
    processing_timestamp: Optional[datetime] = None
    chunk_count: Optional[int] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class DocumentChunk(BaseModel):
    """Document chunk schema."""
    chunk_id: str
    document_id: str
    content: str
    chunk_index: int
    metadata: Dict[str, Any] = Field(default_factory=dict)
    embedding: Optional[List[float]] = None
    
    @validator('content')
    def content_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Content cannot be empty')
        return v


class DocumentUploadRequest(BaseModel):
    """Document upload request schema."""
    filename: str
    content_type: str
    file_size: int
    
    @validator('file_size')
    def validate_file_size(cls, v):
        max_size = 50 * 1024 * 1024  # 50MB
        if v > max_size:
            raise ValueError(f'File size cannot exceed {max_size} bytes')
        return v


class DocumentUploadResponse(BaseModel):
    """Document upload response schema."""
    document_id: str
    filename: str
    status: DocumentStatus
    message: str
    metadata: DocumentMetadata


class DocumentProcessingStatus(BaseModel):
    """Document processing status schema."""
    document_id: str
    status: DocumentStatus
    progress: float = Field(ge=0, le=100)
    message: str
    error_details: Optional[str] = None
    chunks_processed: int = 0
    total_chunks: int = 0


class QueryRequest(BaseModel):
    """RAG query request schema."""
    query: str
    top_k: int = Field(default=3, ge=1, le=20, description="Number of chunks to retrieve")
    similarity_threshold: float = Field(default=0.5, ge=0.0, le=1.0, description="Minimum similarity for retrieved chunks")
    filter_documents: Optional[List[str]] = None
    
    @validator('query')
    def query_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Query cannot be empty')
        return v.strip()


class RetrievedChunk(BaseModel):
    """Retrieved chunk with similarity score."""
    chunk_id: str
    document_id: str
    content: str
    similarity_score: float
    metadata: Dict[str, Any] = Field(default_factory=dict)


class QueryResponse(BaseModel):
    """RAG query response schema."""
    query: str
    answer: str
    retrieved_chunks: List[RetrievedChunk]
    processing_time: float
    total_tokens: Optional[int] = None
    model_used: Optional[str] = None


class HealthCheck(BaseModel):
    """Health check response schema."""
    status: str
    timestamp: datetime
    version: str
    services: Dict[str, str] = Field(default_factory=dict)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ErrorResponse(BaseModel):
    """Error response schema."""
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        } 