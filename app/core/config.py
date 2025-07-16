from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings and configuration."""
    
    # Application Configuration
    app_name: str = Field(default="RAG FinanzAuto", description="Application name")
    app_version: str = Field(default="1.0.0", description="Application version")
    app_host: str = Field(default="0.0.0.0", description="Application host")
    app_port: int = Field(default=8000, description="Application port")
    debug: bool = Field(default=False, description="Debug mode")
    log_level: str = Field(default="INFO", description="Logging level")
    
    # LLM API Keys
    openai_api_key: Optional[str] = Field(default=None, description="OpenAI API key")
    # groq_api_key: Optional[str] = Field(default=None, description="Groq API key")  # Not needed
    # anthropic_api_key: Optional[str] = Field(default=None, description="Anthropic API key")  # Not needed
    
    # Vector Database Configuration
    chroma_persist_directory: str = Field(default="./data/chroma_db", description="Chroma DB persist directory")
    pinecone_api_key: Optional[str] = Field(default=None, description="Pinecone API key")
    pinecone_environment: Optional[str] = Field(default=None, description="Pinecone environment")
    
    # Document Processing - Optimized for better retrieval
    max_file_size_mb: int = Field(default=50, description="Maximum file size in MB")
    chunk_size: int = Field(default=512, description="Text chunk size for processing")  # Reduced for better precision
    chunk_overlap: int = Field(default=100, description="Overlap between chunks")  # Reduced overlap
    
    # RAG Configuration - Optimized for evaluation
    top_k_results: int = Field(default=10, description="Number of top results to retrieve")  # Increased for better recall
    similarity_threshold: float = Field(default=0.5, description="Similarity threshold for retrieval")  # Lowered for more results
    max_tokens: int = Field(default=3000, description="Maximum tokens for LLM response")  # Increased for better answers
    temperature: float = Field(default=0.0, description="LLM temperature")  # Changed from 0.1 to 0.0 for deterministic responses
    
    # Database
    database_url: str = Field(default="sqlite:///./data/app.db", description="Database URL")
    
    # Security
    secret_key: str = Field(default="your-secret-key-here", description="Secret key for JWT")
    access_token_expire_minutes: int = Field(default=30, description="Access token expiration time")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings."""
    return settings 