import os
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncio
from pathlib import Path
import re

import PyPDF2
import markdown
from docx import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from loguru import logger

from app.core.config import settings
from app.models.schemas import (
    DocumentChunk, DocumentMetadata, DocumentStatus, 
    DocumentType, DocumentProcessingStatus
)


class DocumentProcessor:
    """Service for processing documents and extracting text chunks."""
    
    def __init__(self):
        # Improved text splitter with better separators for financial documents
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
            length_function=len,
            separators=[
                "\n\n\n",  # Major section breaks
                "\n\n",    # Paragraph breaks
                ". ",      # Sentence breaks
                "! ",      # Exclamation breaks
                "? ",      # Question breaks
                "; ",      # Semicolon breaks
                ", ",      # Comma breaks
                " ",       # Word breaks
                ""         # Character breaks
            ]
        )
        self.processing_status: Dict[str, DocumentProcessingStatus] = {}
    
    async def process_document(
        self, 
        file_path: str, 
        document_id: str, 
        metadata: DocumentMetadata
    ) -> List[DocumentChunk]:
        """Process a document and return text chunks."""
        try:
            # Update processing status
            self.processing_status[document_id] = DocumentProcessingStatus(
                document_id=document_id,
                status=DocumentStatus.PROCESSING,
                progress=0.0,
                message="Starting document processing",
                chunks_processed=0,
                total_chunks=0
            )
            
            # Extract text based on file type
            document_type = self._get_document_type(metadata.filename)
            text_content = await self._extract_text(file_path, document_type)
            
            # Clean and preprocess text
            text_content = self._preprocess_text(text_content)
            
            # Update progress
            self.processing_status[document_id].progress = 30.0
            self.processing_status[document_id].message = "Text extracted, creating chunks"
            
            # Split text into chunks with improved strategy
            chunks = self._create_chunks(text_content, document_id, metadata)
            
            # Update final status
            self.processing_status[document_id].status = DocumentStatus.COMPLETED
            self.processing_status[document_id].progress = 100.0
            self.processing_status[document_id].message = "Document processing completed"
            self.processing_status[document_id].chunks_processed = len(chunks)
            self.processing_status[document_id].total_chunks = len(chunks)
            
            logger.info(f"Successfully processed document {document_id} into {len(chunks)} chunks")
            return chunks
            
        except Exception as e:
            # Update error status
            self.processing_status[document_id].status = DocumentStatus.FAILED
            self.processing_status[document_id].message = f"Processing failed: {str(e)}"
            self.processing_status[document_id].error_details = str(e)
            
            logger.error(f"Error processing document {document_id}: {str(e)}")
            raise
    
    def _preprocess_text(self, text: str) -> str:
        """Preprocess text for better chunking and quality."""
        # 1. Replace multiple newlines with a single one to consolidate paragraphs
        text = re.sub(r'\n\s*\n', '\n\n', text)
        
        # 2. Join words broken by a hyphen and a newline
        # e.g. "import-\nant" -> "important"
        text = re.sub(r'(\w+)-\n(\w+)', r'\1\2', text)
        
        # 3. Remove excessive whitespace (spaces, tabs) but keep newlines
        text = re.sub(r'[ \t]+', ' ', text)
        
        # 4. Attempt to remove page headers/footers (common in financial docs)
        # This is a heuristic and might need adjustment for specific formats.
        lines = text.split('\n')
        cleaned_lines = []
        for line in lines:
            # Skip lines that look like page numbers or simple headers/footers
            if re.fullmatch(r'\s*Page \d+ (of \d+)?\s*', line, re.IGNORECASE):
                continue
            if re.fullmatch(r'\s*\[\d+\]\s*', line): # e.g., [2]
                continue
            if len(line.strip()) < 10 and re.search(r'\d', line): # Short lines with numbers
                continue
            cleaned_lines.append(line)
        text = '\n'.join(cleaned_lines)
        
        # 5. Remove any remaining non-printable or weird characters
        text = re.sub(r'[^\x20-\x7E\n\t]', ' ', text)
        
        return text.strip()
    
    def _get_document_type(self, filename: str) -> DocumentType:
        """Determine document type from filename."""
        extension = Path(filename).suffix.lower()
        
        type_mapping = {
            '.pdf': DocumentType.PDF,
            '.txt': DocumentType.TXT,
            '.md': DocumentType.MD,
            '.docx': DocumentType.DOCX
        }
        
        if extension not in type_mapping:
            raise ValueError(f"Unsupported file type: {extension}")
        
        return type_mapping[extension]
    
    async def _extract_text(self, file_path: str, document_type: DocumentType) -> str:
        """Extract text from document based on type."""
        try:
            if document_type == DocumentType.PDF:
                return await self._extract_pdf_text(file_path)
            elif document_type == DocumentType.TXT:
                return await self._extract_txt_text(file_path)
            elif document_type == DocumentType.MD:
                return await self._extract_md_text(file_path)
            elif document_type == DocumentType.DOCX:
                return await self._extract_docx_text(file_path)
            else:
                raise ValueError(f"Unsupported document type: {document_type}")
        except Exception as e:
            logger.error(f"Error extracting text from {file_path}: {str(e)}")
            raise
    
    async def _extract_pdf_text(self, file_path: str) -> str:
        """Extract text from PDF file."""
        def extract():
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
                return text
        
        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, extract)
    
    async def _extract_txt_text(self, file_path: str) -> str:
        """Extract text from TXT file."""
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    
    async def _extract_md_text(self, file_path: str) -> str:
        """Extract text from Markdown file."""
        with open(file_path, 'r', encoding='utf-8') as file:
            md_content = file.read()
            # Convert markdown to plain text
            html = markdown.markdown(md_content)
            # Simple HTML tag removal (for basic conversion)
            import re
            text = re.sub(r'<[^>]+>', '', html)
            return text
    
    async def _extract_docx_text(self, file_path: str) -> str:
        """Extract text from DOCX file."""
        def extract():
            doc = Document(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text
        
        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, extract)
    
    def _create_chunks(
        self, 
        text: str, 
        document_id: str, 
        metadata: DocumentMetadata
    ) -> List[DocumentChunk]:
        """Create enhanced chunks with better semantic boundaries."""
        # First, split text using LangChain's text splitter
        text_chunks = self.text_splitter.split_text(text)
        
        # Post-process chunks for better quality
        final_chunks = []
        chunk_index = 0
        
        for chunk_text in text_chunks:
            # Skip chunks that are too short or contain mostly noise after stripping
            cleaned_chunk = chunk_text.strip()
            if len(cleaned_chunk) < 30:  # Minimum meaningful length
                continue
            
            # Optional: A simple noise check can be added here if needed
            # e.g., if self._is_noise_chunk(cleaned_chunk): continue
            
            chunk_id = f"{document_id}_chunk_{chunk_index}"
            
            chunk = DocumentChunk(
                chunk_id=chunk_id,
                document_id=document_id,
                content=cleaned_chunk,
                chunk_index=chunk_index,
                metadata={
                    "filename": metadata.filename,
                    "file_size": metadata.file_size,
                    "content_type": metadata.content_type,
                    "chunk_length": len(cleaned_chunk),
                    "upload_timestamp": metadata.upload_timestamp.isoformat(),
                    # The quality score calculation can be intensive,
                    # consider if it's needed for every chunk.
                    # "chunk_quality_score": self._calculate_chunk_quality(cleaned_chunk)
                }
            )
            final_chunks.append(chunk)
            chunk_index += 1
        
        return final_chunks
    
    def get_processing_status(self, document_id: str) -> Optional[DocumentProcessingStatus]:
        """Get processing status for a document."""
        return self.processing_status.get(document_id)
    
    def cleanup_processing_status(self, document_id: str):
        """Clean up processing status after completion."""
        if document_id in self.processing_status:
            del self.processing_status[document_id]
    
    async def validate_file(self, file_path: str, filename: str) -> bool:
        """Validate uploaded file."""
        try:
            # Check file exists
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")
            
            # Check file size
            file_size = os.path.getsize(file_path)
            max_size = settings.max_file_size_mb * 1024 * 1024
            if file_size > max_size:
                raise ValueError(f"File size exceeds maximum allowed size of {settings.max_file_size_mb}MB")
            
            # Check file type
            self._get_document_type(filename)
            
            return True
            
        except Exception as e:
            logger.error(f"File validation failed for {filename}: {str(e)}")
            raise


# Global document processor instance
document_processor = DocumentProcessor() 