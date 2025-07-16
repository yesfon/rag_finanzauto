# Guía de Desarrollo - RAG FinanzAuto

## Introducción

Este documento contiene información técnica sobre el desarrollo y mantenimiento del sistema RAG FinanzAuto. Es un ejemplo de documento que puede ser procesado por el sistema para demostrar sus capacidades.

## Arquitectura del Sistema

### Componentes Principales

El sistema RAG FinanzAuto está compuesto por los siguientes componentes:

1. **Servicio de Procesamiento de Documentos**
   - Procesa archivos PDF, TXT, MD y DOCX
   - Extrae texto y lo divide en chunks
   - Utiliza LangChain para el procesamiento

2. **Servicio de Embeddings**
   - Genera embeddings usando Sentence-Transformers o OpenAI
   - Cachea embeddings para mejorar el rendimiento
   - Soporta múltiples modelos de embeddings

3. **Base de Datos Vectorial**
   - Utiliza ChromaDB para almacenamiento
   - Búsqueda semántica eficiente
   - Persistencia de datos

4. **Servicio de Consultas RAG**
   - Procesa consultas en lenguaje natural
   - Implementa búsqueda semántica con ranking
   - Integra con OpenAI LLM

### Flujo de Datos

1. **Ingesta de Documentos**
   - Usuario sube documento a través de la API
   - Sistema procesa el documento y extrae texto
   - Texto se divide en chunks semánticamente coherentes
   - Se generan embeddings para cada chunk
   - Chunks y embeddings se almacenan en ChromaDB

2. **Procesamiento de Consultas**
   - Usuario envía consulta en lenguaje natural
   - Sistema genera embedding para la consulta
   - Se realiza búsqueda semántica en ChromaDB
   - Se recuperan chunks más relevantes
   - Se re-rankean los resultados
   - LLM genera respuesta basada en el contexto

## Configuración y Deployment

### Variables de Entorno

El sistema utiliza las siguientes variables de entorno:

- `OPENAI_API_KEY`: Clave de API de OpenAI (requerida)
- `CHUNK_SIZE`: Tamaño de chunks (por defecto 1000)
- `CHUNK_OVERLAP`: Solapamiento entre chunks (por defecto 200)
- `TOP_K_RESULTS`: Número de resultados a recuperar (por defecto 5)
- `SIMILARITY_THRESHOLD`: Umbral de similitud (por defecto 0.7)

### Instalación con Miniconda

Para instalar el sistema usando Miniconda:

```bash
# Crear entorno
conda env create -f environment.yml

# Activar entorno
conda activate rag_finanzauto

# Configurar variables de entorno
cp env.example .env
# Editar .env con tus API keys

# Ejecutar aplicación
python app/main.py
```

### Deployment con Docker

Para deployment en producción:

```bash
# Construir imagen
docker build -t rag-finanzauto .

# Ejecutar con Docker Compose
docker-compose up -d
```

## APIs y Endpoints

### Documentos

- `POST /api/v1/documents/upload`: Subir documento
- `GET /api/v1/documents/status/{id}`: Estado del procesamiento
- `GET /api/v1/documents/{id}/chunks`: Obtener chunks
- `DELETE /api/v1/documents/{id}`: Eliminar documento

### Consultas

- `POST /api/v1/query/`: Procesar consulta RAG
- `GET /api/v1/query/history`: Historial de consultas
- `GET /api/v1/query/stats`: Estadísticas del servicio

### Salud del Sistema

- `GET /api/v1/health/`: Health check básico
- `GET /api/v1/health/detailed`: Health check detallado

## Mejores Prácticas

### Optimización de Chunks

- Usar chunks de 1000 tokens con overlap de 200
- Considerar la estructura del documento
- Mantener coherencia semántica

### Configuración de Embeddings

- OpenAI para máxima calidad
- Sentence-Transformers para uso offline
- Considerar el costo vs. calidad

### Monitoreo

- Supervisar tiempo de respuesta
- Monitorear uso de memoria
- Verificar estado de servicios externos

## Troubleshooting

### Problemas Comunes

1. **Error de API Key**
   - Verificar que las claves estén configuradas
   - Comprobar límites de uso

2. **Problemas de Memoria**
   - Reducir tamaño de chunks
   - Aumentar límites de memoria

3. **Latencia Alta**
   - Optimizar embeddings
   - Usar caché agresivo
   - Considerar modelos más rápidos

### Logs y Debugging

El sistema genera logs detallados en:
- Consola (desarrollo)
- Archivo de log (producción)
- Métricas en Prometheus

## Evaluación y Métricas

### Métricas de Relevancia

- Precision@K
- Recall@K
- NDCG
- MRR

### Métricas de Calidad

- BLEU Score
- ROUGE Score
- BERTScore
- Coherencia semántica

### Métricas de Rendimiento

- Tiempo de respuesta
- Throughput
- Uso de recursos
- Disponibilidad

## Conclusión

Este sistema RAG proporciona una solución robusta para asistencia de conocimiento basada en documentos. Con su arquitectura modular y integración con OpenAI, es escalable y adaptable a diferentes casos de uso.

Para más información, consulta la documentación completa en el README.md del proyecto. 