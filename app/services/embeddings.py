import os
import time
from typing import List, Optional
import numpy as np
import openai
from loguru import logger
import re

from app.core.config import settings


class EmbeddingService:
    """Service for generating and managing text embeddings."""
    
    def __init__(self):
        self.openai_client = None
        self.embedding_model = "text-embedding-3-large"  # Better multilingual support
        self._initialize_clients()
    
    def _initialize_clients(self):
        """Initialize API clients."""
        if settings.openai_api_key:
            self.openai_client = openai.OpenAI(api_key=settings.openai_api_key)
            logger.info("Initialized OpenAI embeddings client")
        else:
            logger.warning("No OpenAI API key provided for embeddings")
    
    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts."""
        try:
            if not self.openai_client:
                raise ValueError("OpenAI client not initialized")
            
            # Preprocess texts for better embeddings
            processed_texts = [self._preprocess_text_for_embedding(text) for text in texts]
            
            # Generate embeddings
            embeddings = []
            batch_size = 10  # Process in batches to avoid rate limits
            
            for i in range(0, len(processed_texts), batch_size):
                batch = processed_texts[i:i + batch_size]
                
                response = self.openai_client.embeddings.create(
                    model=self.embedding_model,
                    input=batch,
                    encoding_format="float"
                )
                
                batch_embeddings = [embedding.embedding for embedding in response.data]
                embeddings.extend(batch_embeddings)
                
                # Small delay to avoid rate limits
                if i + batch_size < len(processed_texts):
                    time.sleep(0.1)
            
            logger.info(f"Generated {len(embeddings)} embeddings using OpenAI")
            return embeddings
            
        except Exception as e:
            logger.error(f"Error generating embeddings: {str(e)}")
            raise
    
    async def generate_query_embedding(self, query: str) -> List[float]:
        """Generate embedding for a single query."""
        try:
            if not self.openai_client:
                raise ValueError("OpenAI client not initialized")
            
            # Preprocess query for better embedding
            processed_query = self._preprocess_text_for_embedding(query)
            
            response = self.openai_client.embeddings.create(
                model=self.embedding_model,
                input=processed_query,
                encoding_format="float"
            )
            
            embedding = response.data[0].embedding
            logger.info(f"Generated embedding for query: {query[:50]}...")
            return embedding
            
        except Exception as e:
            logger.error(f"Error generating query embedding: {str(e)}")
            raise
    
    def _preprocess_text_for_embedding(self, text: str) -> str:
        """Preprocess text for better embedding generation."""
        if not text:
            return ""
        
        # Convert to lowercase for consistency
        processed = text.lower()
        
        # Remove excessive whitespace
        processed = re.sub(r'\s+', ' ', processed)
        
        # Remove common noise characters but keep important punctuation
        processed = re.sub(r'[^\w\s\.\,\!\?\;\:\-\(\)\[\]\{\}\'\"]', ' ', processed)
        
        # Normalize Polish characters (if needed)
        polish_mappings = {
            'ą': 'a', 'ć': 'c', 'ę': 'e', 'ł': 'l', 'ń': 'n', 
            'ó': 'o', 'ś': 's', 'ź': 'z', 'ż': 'z'
        }
        
        for polish_char, latin_char in polish_mappings.items():
            processed = processed.replace(polish_char, latin_char)
        
        # Remove very short words (likely noise)
        words = processed.split()
        filtered_words = [word for word in words if len(word) > 1]
        
        # Limit length to avoid token limits
        if len(filtered_words) > 8000:  # Conservative limit
            filtered_words = filtered_words[:8000]
        
        return ' '.join(filtered_words)
    
    def calculate_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Calculate cosine similarity between two embeddings."""
        try:
            if not embedding1 or not embedding2:
                return 0.0
            
            # Convert to numpy arrays
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)
            
            # Calculate cosine similarity
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            similarity = dot_product / (norm1 * norm2)
            return float(similarity)
            
        except Exception as e:
            logger.error(f"Error calculating similarity: {str(e)}")
            return 0.0
    
    def calculate_similarities(
        self, 
        query_embedding: List[float], 
        document_embeddings: List[List[float]]
    ) -> List[float]:
        """Calculate similarities between query and multiple document embeddings."""
        try:
            similarities = []
            for doc_embedding in document_embeddings:
                similarity = self.calculate_similarity(query_embedding, doc_embedding)
                similarities.append(similarity)
            
            return similarities
            
        except Exception as e:
            logger.error(f"Error calculating similarities: {str(e)}")
            return [0.0] * len(document_embeddings)
    
    def normalize_embeddings(self, embeddings: List[List[float]]) -> List[List[float]]:
        """Normalize embeddings to unit vectors."""
        try:
            normalized = []
            for embedding in embeddings:
                vec = np.array(embedding)
                norm = np.linalg.norm(vec)
                if norm > 0:
                    normalized.append((vec / norm).tolist())
                else:
                    normalized.append(embedding)  # Keep original if zero vector
            
            return normalized
            
        except Exception as e:
            logger.error(f"Error normalizing embeddings: {str(e)}")
            return embeddings
    
    def get_embedding_dimension(self) -> int:
        """Get the dimension of embeddings generated by this service."""
        # text-embedding-3-large has 3072 dimensions
        return 3072
    
    def get_service_stats(self) -> dict:
        """Get service statistics."""
        return {
            "embedding_model": self.embedding_model,
            "embedding_dimension": self.get_embedding_dimension(),
            "openai_client_available": self.openai_client is not None
        }


# Global embedding service instance
embedding_service = EmbeddingService() 