import time
from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncio
import re

from loguru import logger

from app.core.config import settings
from app.models.schemas import (
    QueryRequest, QueryResponse, RetrievedChunk, DocumentChunk
)
from app.services.embeddings import embedding_service
from app.services.vector_store import vector_store
from app.services.llm_service import llm_service


class RAGService:
    """Service for Retrieval-Augmented Generation queries."""
    
    def __init__(self):
        self.query_history: List[Dict[str, Any]] = []
        self.max_history_size = 1000
    
    async def process_query(self, query_request: QueryRequest) -> QueryResponse:
        """Process a RAG query and return response."""
        start_time = time.time()
        
        try:
            logger.info(f"Processing RAG query: {query_request.query[:100]}...")

            # --- Intent Detection for Summarization ---
            summary_keywords = [
                "resume", "resumen", "summary", "sumariza", "de qué se trata", 
                "acerca de qué es", "tema principal", "idea general"
            ]
            query_lower = query_request.query.lower()
            is_summary_query = any(keyword in query_lower for keyword in summary_keywords)
            
            unique_docs = await vector_store.get_unique_document_ids()
            
            if is_summary_query and len(unique_docs) == 1:
                logger.info("Summary query detected for a single document. Switching to summarization mode.")
                doc_id = unique_docs[0]['document_id']
                
                summary_data = await self.get_document_summary(doc_id)
                
                return QueryResponse(
                    query=query_request.query,
                    answer=summary_data.get("summary", "No se pudo generar el resumen."),
                    retrieved_chunks=[],
                    processing_time=time.time() - start_time,
                    total_tokens=summary_data.get("total_tokens"),
                    model_used=summary_data.get("model_used")
                )
            # --- End of Intent Detection ---

            query_embedding = await embedding_service.generate_query_embedding(
                query_request.query
            )
            
            candidate_chunks = await vector_store.search_similar_chunks(
                query_embedding=query_embedding,
                top_k=20,
                similarity_threshold=0.2,
                filter_documents=query_request.filter_documents
            )
            
            if len(candidate_chunks) > 1:
                reranked_chunks = await self._enhanced_rerank_chunks(
                    query_request.query, candidate_chunks
                )
            else:
                reranked_chunks = candidate_chunks
            
            final_chunks = reranked_chunks[:query_request.top_k]
            
            context = self._prepare_context(final_chunks)
            conversation_history = self._prepare_conversation_history()

            answer, model_used, total_tokens = await llm_service.generate_answer(
                query=query_request.query,
                context=context,
                conversation_history=conversation_history,
                max_tokens=settings.max_tokens,
                temperature=settings.temperature
            )
            
            processing_time = time.time() - start_time
            
            response = QueryResponse(
                query=query_request.query,
                answer=answer,
                retrieved_chunks=final_chunks,
                processing_time=processing_time,
                total_tokens=total_tokens,
                model_used=model_used
            )
            
            self._add_to_history(query_request, response)
            
            logger.info(f"RAG query processed successfully in {processing_time:.2f}s")
            return response
            
        except Exception as e:
            logger.error(f"Error processing RAG query: {str(e)}")
            raise
    
    async def _enhanced_rerank_chunks(
        self, 
        query: str, 
        chunks: List[RetrievedChunk]
    ) -> List[RetrievedChunk]:
        """Enhanced re-ranking using multiple factors, ignoring stop words."""
        try:
            stop_words = set([
                "de", "la", "que", "el", "en", "y", "a", "los", "del", "se", "con", "por", 
                "su", "para", "como", "un", "una", "al", "lo", "las", "o", "sus", "si",
                "qué", "cual", "cuando", "donde", "quien", "es", "son", "fue", "era"
            ])
            
            query_terms = set(
                word for word in re.findall(r'\b\w+\b', query.lower()) 
                if word not in stop_words
            )
            if not query_terms:
                query_terms = set(re.findall(r'\b\w+\b', query.lower()))

            for chunk in chunks:
                chunk_terms = set(re.findall(r'\b\w+\b', chunk.content.lower()))
                
                term_overlap = len(query_terms.intersection(chunk_terms))
                term_overlap_score = term_overlap / max(len(query_terms), 1)
                
                exact_matches = 0
                for term in query_terms:
                    if len(term) > 2:
                        exact_matches += chunk.content.lower().count(term)
                exact_match_score = min(exact_matches / max(len(query_terms), 1), 1.0)
                
                position_score = 0
                if term_overlap > 0:
                    first_match_pos = float('inf')
                    for term in query_terms:
                        pos = chunk.content.lower().find(term)
                        if pos != -1 and pos < first_match_pos:
                            first_match_pos = pos
                    if first_match_pos != float('inf'):
                        position_score = 1.0 / (1.0 + first_match_pos / 100.0)
                
                length_score = min(len(chunk.content) / 500.0, 1.0)
                
                final_score = (
                    chunk.similarity_score * 0.60 +
                    term_overlap_score * 0.15 +
                    exact_match_score * 0.15 +
                    position_score * 0.05 +
                    length_score * 0.05
                )
                
                chunk.similarity_score = final_score
            
            chunks.sort(key=lambda x: x.similarity_score, reverse=True)
            
            logger.info(f"Enhanced re-ranked {len(chunks)} chunks")
            return chunks
            
        except Exception as e:
            logger.warning(f"Error in enhanced re-ranking: {str(e)}")
            return chunks
    
    def _prepare_context(self, chunks: List[RetrievedChunk]) -> str:
        """Prepare context string from retrieved chunks."""
        context_parts = []
        
        for i, chunk in enumerate(chunks):
            source_info = ""
            if chunk.metadata and 'filename' in chunk.metadata:
                source_info = f"(Source: {chunk.metadata['filename']}, Chunk: {chunk.metadata.get('chunk_index', 'N/A')})"
            
            context_parts.append(f"Fragment {i+1} {source_info}:\n{chunk.content}")
        
        return "\n\n---\n\n".join(context_parts)

    def _prepare_conversation_history(self, last_n: int = 5) -> str:
        """Prepare a string with the last N interactions."""
        if not self.query_history:
            return "No hay historial de conversación previo."

        history = self.get_query_history(limit=last_n)
        
        history_parts = []
        for interaction in history:
            history_parts.append(f"Usuario: {interaction['query']}\nAsistente: {interaction['answer']}")
            
        return "\n\n---\n\n".join(history_parts)
    
    def _add_to_history(self, query_request: QueryRequest, response: QueryResponse):
        """Add query to history."""
        history_entry = {
            "timestamp": datetime.now().isoformat(),
            "query": query_request.query,
            "answer": response.answer,
            "num_retrieved_chunks": len(response.retrieved_chunks),
            "processing_time": response.processing_time,
            "model_used": response.model_used,
            "total_tokens": response.total_tokens
        }
        
        self.query_history.append(history_entry)
        
        if len(self.query_history) > self.max_history_size:
            self.query_history = self.query_history[-self.max_history_size:]
    
    def get_query_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent query history."""
        return self.query_history[-limit:]
    
    def clear_history(self):
        """Clear query history."""
        self.query_history.clear()
        logger.info("Cleared query history")
    
    async def get_document_summary(self, document_id: str) -> Dict[str, Any]:
        """Get summary of a specific document."""
        try:
            chunks = await vector_store.get_document_chunks(document_id)
            
            if not chunks:
                return {"error": "Document not found"}
            
            content = "\n".join([chunk['content'] for chunk in chunks])
            
            summary_query = "Please provide a comprehensive summary of this document."
            summary, model_used, total_tokens = await llm_service.generate_answer(
                query=summary_query,
                context=content,
                conversation_history="No hay historial previo para esta consulta de resumen.",
                max_tokens=500,
                temperature=0.1
            )
            
            return {
                "document_id": document_id,
                "summary": summary,
                "total_chunks": len(chunks),
                "total_content_length": len(content),
                "model_used": model_used,
                "total_tokens": total_tokens
            }
            
        except Exception as e:
            logger.error(f"Error generating document summary: {str(e)}")
            return {"error": str(e)}

rag_service = RAGService() 