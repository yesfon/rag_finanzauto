import os
import time
from typing import Optional, Tuple
import openai
from loguru import logger

from app.core.config import settings


class LLMService:
    """Service for interacting with Large Language Models."""
    
    def __init__(self):
        self.openai_client = None
        self._initialize_clients()
    
    def _initialize_clients(self):
        """Initialize API clients."""
        if settings.openai_api_key:
            self.openai_client = openai.OpenAI(api_key=settings.openai_api_key)
            logger.info("Initialized OpenAI client")
        else:
            logger.warning("No OpenAI API key provided")
    
    async def generate_answer(
        self, 
        query: str, 
        context: str, 
        conversation_history: str,
        max_tokens: int = 2000,
        temperature: float = 0.1
    ) -> Tuple[str, str, Optional[int]]:
        """Generate answer using available LLM services."""
        try:
            if self.openai_client:
                return await self._generate_openai_response(
                    query, context, conversation_history, max_tokens, temperature
                )
            else:
                return "No LLM service available. Please configure API keys.", "none", 0
                
        except Exception as e:
            logger.error(f"Error generating answer: {str(e)}")
            return f"Error generating answer: {str(e)}", "error", 0
    
    async def _generate_openai_response(
        self, 
        query: str, 
        context: str, 
        conversation_history: str,
        max_tokens: int,
        temperature: float
    ) -> Tuple[str, str, Optional[int]]:
        """Generate response using OpenAI."""
        try:
            # The system prompt is now standardized and robust.
            system_prompt = """Eres un asistente experto de RAG FinanzAuto, especializado en analizar y responder preguntas sobre documentos financieros y técnicos. Tu propósito es proporcionar respuestas precisas y concisas basadas EXCLUSIVAMENTE en el contexto que se te proporciona y el historial de la conversación.

Instrucciones Clave:
1.  **Fuente de Verdad**: Basa todas tus respuestas estrictamente en el 'Contexto de Documentos' y el 'Historial de Conversación'. No utilices conocimiento externo.
2.  **Continuidad**: Utiliza el 'Historial de Conversación' para entender preguntas de seguimiento y referencias ambiguas (ej. "y sobre el otro tema...", "explica más").
3.  **Precisión y Relevancia**: Céntrate en responder directamente a la 'Pregunta del usuario'. Evita información superflua.
4.  **Manejo de Incertidumbre**: Si la respuesta no se encuentra en ninguna de las fuentes, responde de forma clara: "No he encontrado información suficiente en los documentos para responder a esa pregunta."
5.  **Síntesis Coherente**: Si el contexto proviene de múltiples fragmentos, sintetiza la información en una respuesta unificada y coherente.
6.  **Formato Profesional**: Utiliza formato Markdown (negritas, listas) para estructurar la respuesta y mejorar la legibilidad.
7.  **Idioma**: Responde siempre en el mismo idioma que la 'Pregunta del usuario'."""
            
            # The user message template is also standardized.
            user_message = f"""**Historial de Conversación:**
{conversation_history}

**Contexto de Documentos:**
{context}

**Pregunta del usuario:**
{query}

**Respuesta:**"""
            
            # Generate response
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            answer = response.choices[0].message.content
            model_used = "gpt-4o"
            total_tokens = response.usage.total_tokens if response.usage else None
            
            logger.info(f"Generated response using OpenAI ({total_tokens} tokens)")
            return answer, model_used, total_tokens
            
        except Exception as e:
            logger.error(f"Error generating OpenAI response: {str(e)}")
            raise

    def get_service_stats(self) -> dict:
        """Get service statistics."""
        return {
            "llm_provider": "OpenAI" if self.openai_client else "None",
            "default_model": "gpt-4o", 
            "openai_client_available": self.openai_client is not None
        }


# Global LLM service instance
llm_service = LLMService() 