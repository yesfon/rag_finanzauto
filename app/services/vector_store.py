import os
import uuid
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import asyncio

import chromadb
from chromadb.config import Settings as ChromaSettings
from chromadb.utils import embedding_functions
from loguru import logger

from app.core.config import settings
from app.models.schemas import DocumentChunk, RetrievedChunk
from app.services.embeddings import embedding_service


class VectorStore:
    """Vector database service using ChromaDB."""
    
    def __init__(self):
        self.client = None
        self.collection = None
        self.collection_name = "rag_documents"
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize ChromaDB client."""
        try:
            # Create data directory if it doesn't exist
            os.makedirs(settings.chroma_persist_directory, exist_ok=True)
            
            # Initialize ChromaDB client with persistence
            self.client = chromadb.PersistentClient(
                path=settings.chroma_persist_directory,
                settings=ChromaSettings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            # Get or create collection
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}  # Use cosine distance for similarity
            )
            
            logger.info(f"Initialized ChromaDB client with collection: {self.collection_name}")
            logger.info(f"Collection count: {self.collection.count()}")
            
        except Exception as e:
            logger.error(f"Error initializing ChromaDB client: {str(e)}")
            raise
    
    def cleanup_on_startup(self):
        """Clean up any residual data on startup (optional)."""
        try:
            if settings.debug:
                # In debug mode, optionally clean up old data
                count = self.collection.count()
                if count > 0:
                    logger.info(f"Found {count} existing chunks in collection")
                    logger.info("To clean up, call reset_collection() or use the frontend reset button")
        except Exception as e:
            logger.warning(f"Error during startup cleanup: {str(e)}")
    
    def force_cleanup(self):
        """Force cleanup of all data (use with caution)."""
        try:
            # Delete the entire collection and recreate it
            try:
                self.client.delete_collection(self.collection_name)
                logger.info(f"Deleted existing collection: {self.collection_name}")
            except Exception:
                logger.info("No existing collection to delete")
            
            # Recreate the collection
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            
            logger.info(f"Created fresh collection: {self.collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error during force cleanup: {str(e)}")
            return False
    
    async def add_chunks(self, chunks: List[DocumentChunk]) -> bool:
        """Add document chunks to the vector store."""
        try:
            if not chunks:
                logger.warning("No chunks provided to add to vector store")
                return False
            
            # Prepare data for ChromaDB
            ids = [chunk.chunk_id for chunk in chunks]
            documents = [chunk.content for chunk in chunks]
            embeddings = [chunk.embedding for chunk in chunks if chunk.embedding]
            metadatas = [self._prepare_metadata(chunk) for chunk in chunks]
            
            # Validate embeddings
            if len(embeddings) != len(chunks):
                logger.error("Not all chunks have embeddings")
                return False
            
            # Add to collection in batches to avoid memory issues
            batch_size = 100
            for i in range(0, len(chunks), batch_size):
                batch_end = min(i + batch_size, len(chunks))
                
                batch_ids = ids[i:batch_end]
                batch_documents = documents[i:batch_end]
                batch_embeddings = embeddings[i:batch_end]
                batch_metadatas = metadatas[i:batch_end]
                
                # Add batch to collection
                await self._add_batch_async(
                    batch_ids, batch_documents, batch_embeddings, batch_metadatas
                )
                
                logger.info(f"Added batch {i//batch_size + 1} ({len(batch_ids)} chunks)")
            
            logger.info(f"Successfully added {len(chunks)} chunks to vector store")
            return True
            
        except Exception as e:
            logger.error(f"Error adding chunks to vector store: {str(e)}")
            raise
    
    async def _add_batch_async(
        self, 
        ids: List[str], 
        documents: List[str], 
        embeddings: List[List[float]], 
        metadatas: List[Dict[str, Any]]
    ):
        """Add a batch of documents asynchronously."""
        def add_batch():
            self.collection.add(
                ids=ids,
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas
            )
        
        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, add_batch)
    
    def _prepare_metadata(self, chunk: DocumentChunk) -> Dict[str, Any]:
        """Prepare metadata for ChromaDB storage."""
        metadata = {
            "document_id": chunk.document_id,
            "chunk_index": chunk.chunk_index,
            "chunk_length": len(chunk.content),
            **chunk.metadata
        }
        
        # ChromaDB doesn't support nested objects, so flatten if needed
        flattened = {}
        for key, value in metadata.items():
            if isinstance(value, (str, int, float, bool)):
                flattened[key] = value
            else:
                flattened[key] = str(value)
        
        return flattened
    
    async def search_similar_chunks(
        self, 
        query_embedding: List[float], 
        top_k: int = 5,
        similarity_threshold: float = 0.7,
        filter_documents: Optional[List[str]] = None
    ) -> List[RetrievedChunk]:
        """Search for similar chunks using vector similarity."""
        try:
            # Prepare query filters
            where_filter = None
            if filter_documents:
                where_filter = {"document_id": {"$in": filter_documents}}
            
            # Perform similarity search
            results = await self._query_async(
                query_embedding=query_embedding,
                n_results=top_k,
                where=where_filter
            )
            
            # Process results
            retrieved_chunks = []
            if results and results['ids'] and results['ids'][0]:
                for i, chunk_id in enumerate(results['ids'][0]):
                    # Calculate similarity score (ChromaDB returns distances)
                    distance = results['distances'][0][i]
                    similarity_score = 1 - distance  # Convert distance to similarity
                    
                    # Filter by similarity threshold
                    if similarity_score >= similarity_threshold:
                        retrieved_chunk = RetrievedChunk(
                            chunk_id=chunk_id,
                            document_id=results['metadatas'][0][i]['document_id'],
                            content=results['documents'][0][i],
                            similarity_score=similarity_score,
                            metadata=results['metadatas'][0][i]
                        )
                        retrieved_chunks.append(retrieved_chunk)
            
            # Sort by similarity score (descending)
            retrieved_chunks.sort(key=lambda x: x.similarity_score, reverse=True)
            
            logger.info(f"Found {len(retrieved_chunks)} similar chunks (threshold: {similarity_threshold})")
            return retrieved_chunks
            
        except Exception as e:
            logger.error(f"Error searching similar chunks: {str(e)}")
            raise
    
    async def _query_async(
        self, 
        query_embedding: List[float], 
        n_results: int,
        where: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Perform async query on ChromaDB."""
        def query():
            return self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=where,
                include=['documents', 'metadatas', 'distances']
            )
        
        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, query)
    
    async def delete_document_chunks(self, document_id: str) -> bool:
        """Delete all chunks for a specific document."""
        try:
            def delete_chunks():
                self.collection.delete(
                    where={"document_id": document_id}
                )
            
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, delete_chunks)
            
            logger.info(f"Deleted chunks for document: {document_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting document chunks: {str(e)}")
            raise
    
    async def get_document_chunks(self, document_id: str) -> List[Dict[str, Any]]:
        """Get all chunks for a specific document."""
        try:
            def get_chunks():
                return self.collection.get(
                    where={"document_id": document_id},
                    include=['documents', 'metadatas']
                )
            
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(None, get_chunks)
            
            chunks = []
            if results and results['ids']:
                for i, chunk_id in enumerate(results['ids']):
                    chunk_data = {
                        'chunk_id': chunk_id,
                        'content': results['documents'][i],
                        'metadata': results['metadatas'][i]
                    }
                    chunks.append(chunk_data)
            
            logger.info(f"Retrieved {len(chunks)} chunks for document: {document_id}")
            return chunks
            
        except Exception as e:
            logger.error(f"Error retrieving document chunks: {str(e)}")
            raise
    
    async def get_unique_document_ids(self) -> List[Dict[str, Any]]:
        """Get list of unique documents with their metadata."""
        try:
            def get_all_metadata():
                return self.collection.get(
                    include=['metadatas']
                )
            
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(None, get_all_metadata)
            
            # Group by document_id to get unique documents
            unique_docs = {}
            if results and results['metadatas']:
                for metadata in results['metadatas']:
                    doc_id = metadata.get('document_id')
                    if doc_id and doc_id not in unique_docs:
                        unique_docs[doc_id] = {
                            'document_id': doc_id,
                            'filename': metadata.get('filename', 'Unknown'),
                            'upload_timestamp': metadata.get('upload_timestamp', 'Unknown'),
                            'chunk_count': 0
                        }
                    
                    # Count chunks for this document
                    if doc_id in unique_docs:
                        unique_docs[doc_id]['chunk_count'] += 1
            
            # Convert to list and sort by upload time
            unique_docs_list = list(unique_docs.values())
            unique_docs_list.sort(key=lambda x: x.get('upload_timestamp', ''), reverse=True)
            
            logger.info(f"Found {len(unique_docs_list)} unique documents")
            return unique_docs_list
            
        except Exception as e:
            logger.error(f"Error retrieving unique document IDs: {str(e)}")
            raise
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector store collection."""
        try:
            count = self.collection.count()
            
            stats = {
                "collection_name": self.collection_name,
                "total_chunks": count,
                "embedding_dimension": embedding_service.get_embedding_dimension(),
                "embedding_model": embedding_service.embedding_model,
                "persist_directory": settings.chroma_persist_directory
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting collection stats: {str(e)}")
            return {}
    
    async def reset_collection(self) -> bool:
        """Reset the entire collection (delete all data)."""
        try:
            def reset():
                self.client.delete_collection(self.collection_name)
                self.collection = self.client.create_collection(
                    name=self.collection_name,
                    metadata={"hnsw:space": "cosine"}
                )
            
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, reset)
            
            logger.info("Reset vector store collection")
            return True
            
        except Exception as e:
            logger.error(f"Error resetting collection: {str(e)}")
            raise
    
    def health_check(self) -> Dict[str, Any]:
        """Check the health of the vector store."""
        try:
            count = self.collection.count()
            return {
                "status": "healthy",
                "collection_name": self.collection_name,
                "total_chunks": count,
                "client_type": "ChromaDB"
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "client_type": "ChromaDB"
            }


# Global vector store instance
vector_store = VectorStore() 