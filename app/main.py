from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from contextlib import asynccontextmanager
import uvicorn

from app.core.config import settings
from app.core.logging import app_logger
from app.api import documents, query, health, embeddings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    app_logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    app_logger.info(f"Debug mode: {settings.debug}")
    
    # Initialize services (they're already initialized as global instances)
    app_logger.info("Services initialized successfully")
    
    yield
    
    # Shutdown
    app_logger.info("Shutting down application")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="RAG (Retrieval-Augmented Generation) system for developer knowledge assistance",
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add Prometheus metrics
from starlette_prometheus import PrometheusMiddleware, metrics
app.add_middleware(PrometheusMiddleware)
app.add_route("/metrics", metrics)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(health.router, prefix="/api/v1")
app.include_router(documents.router, prefix="/api/v1")
app.include_router(query.router, prefix="/api/v1")
app.include_router(embeddings.router, prefix="/api/v1")

# Mount static files for frontend
try:
    app.mount("/static", StaticFiles(directory="frontend/static"), name="static")
except Exception as e:
    app_logger.warning(f"Could not mount static files: {e}")


@app.get("/", response_class=HTMLResponse)
async def root():
    """Root endpoint - serve the frontend."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>RAG FinanzAuto</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                margin: 0;
                padding: 20px;
                background-color: #f5f5f5;
            }
            .container {
                max-width: 1200px;
                margin: 0 auto;
                background: white;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            h1 {
                color: #2c3e50;
                text-align: center;
                margin-bottom: 30px;
            }
            .section {
                margin-bottom: 30px;
                padding: 20px;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
            }
            .section h2 {
                color: #34495e;
                margin-top: 0;
            }
            .api-link {
                display: inline-block;
                margin: 10px 10px 10px 0;
                padding: 10px 20px;
                background-color: #3498db;
                color: white;
                text-decoration: none;
                border-radius: 5px;
                transition: background-color 0.3s;
            }
            .api-link:hover {
                background-color: #2980b9;
            }
            .upload-section {
                background-color: #ecf0f1;
                padding: 20px;
                border-radius: 8px;
                margin: 20px 0;
            }
            .query-section {
                background-color: #e8f5e8;
                padding: 20px;
                border-radius: 8px;
                margin: 20px 0;
            }
            input[type="file"], input[type="text"], textarea {
                width: 100%;
                padding: 10px;
                margin: 10px 0;
                border: 1px solid #ddd;
                border-radius: 4px;
                box-sizing: border-box;
            }
            button {
                background-color: #27ae60;
                color: white;
                padding: 12px 24px;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                font-size: 16px;
            }
            button:hover {
                background-color: #219a52;
            }
            .result {
                margin-top: 20px;
                padding: 15px;
                background-color: #f8f9fa;
                border-radius: 4px;
                border-left: 4px solid #007bff;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚀 RAG FinanzAuto</h1>
            <p style="text-align: center; color: #666; font-size: 18px;">
                Retrieval-Augmented Generation System for Developer Knowledge
            </p>
            
            <div class="section">
                <h2>📚 Document Upload</h2>
                <div class="upload-section">
                    <p>Upload documents (PDF, TXT, MD, DOCX) to build your knowledge base:</p>
                    <input type="file" id="fileInput" accept=".pdf,.txt,.md,.docx">
                    <button onclick="uploadDocument()">Upload Document</button>
                    <div id="uploadResult" class="result" style="display: none;"></div>
                </div>
            </div>
            
            <div class="section">
                <h2>🔍 Query Interface</h2>
                <div class="query-section">
                    <p>Ask questions about your uploaded documents:</p>
                    <textarea id="queryInput" placeholder="Enter your question here..." rows="3"></textarea>
                    <button onclick="submitQuery()">Submit Query</button>
                    <div id="queryResult" class="result" style="display: none;"></div>
                </div>
            </div>
            
            <div class="section">
                <h2>🔗 API Documentation</h2>
                <p>Explore the available API endpoints:</p>
                <a href="/docs" class="api-link">📖 Swagger UI</a>
                <a href="/redoc" class="api-link">📋 ReDoc</a>
                <a href="/api/v1/health" class="api-link">❤️ Health Check</a>
            </div>
            
            <div class="section">
                <h2>📊 System Information</h2>
                <p>Current system status and statistics:</p>
                <button onclick="getSystemInfo()">Get System Info</button>
                <div id="systemInfo" class="result" style="display: none;"></div>
            </div>
        </div>
        
        <script>
            async function uploadDocument() {
                const fileInput = document.getElementById('fileInput');
                const resultDiv = document.getElementById('uploadResult');
                
                if (!fileInput.files[0]) {
                    alert('Please select a file first');
                    return;
                }
                
                const formData = new FormData();
                formData.append('file', fileInput.files[0]);
                
                try {
                    resultDiv.style.display = 'block';
                    resultDiv.innerHTML = '⏳ Uploading document...';
                    
                    const response = await fetch('/api/v1/documents/upload', {
                        method: 'POST',
                        body: formData
                    });
                    
                    const result = await response.json();
                    
                    if (response.ok) {
                        resultDiv.innerHTML = `✅ Document uploaded successfully!<br>
                                             <strong>ID:</strong> ${result.document_id}<br>
                                             <strong>Status:</strong> ${result.status}<br>
                                             <strong>Message:</strong> ${result.message}`;
                    } else {
                        resultDiv.innerHTML = `❌ Error: ${result.detail}`;
                    }
                } catch (error) {
                    resultDiv.innerHTML = `❌ Error: ${error.message}`;
                }
            }
            
            async function submitQuery() {
                const queryInput = document.getElementById('queryInput');
                const resultDiv = document.getElementById('queryResult');
                
                if (!queryInput.value.trim()) {
                    alert('Please enter a query');
                    return;
                }
                
                try {
                    resultDiv.style.display = 'block';
                    resultDiv.innerHTML = '⏳ Processing query...';
                    
                    const response = await fetch('/api/v1/query/', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            query: queryInput.value,
                            top_k: 5,
                            similarity_threshold: 0.7
                        })
                    });
                    
                    const result = await response.json();
                    
                    if (response.ok) {
                        resultDiv.innerHTML = `
                            <strong>Query:</strong> ${result.query}<br><br>
                            <strong>Answer:</strong><br>
                            <div style="background: white; padding: 15px; border-radius: 4px; margin: 10px 0;">
                                ${result.answer}
                            </div>
                            <strong>Retrieved chunks:</strong> ${result.retrieved_chunks.length}<br>
                            <strong>Processing time:</strong> ${result.processing_time.toFixed(2)}s<br>
                            <strong>Model used:</strong> ${result.model_used}
                        `;
                    } else {
                        resultDiv.innerHTML = `❌ Error: ${result.detail}`;
                    }
                } catch (error) {
                    resultDiv.innerHTML = `❌ Error: ${error.message}`;
                }
            }
            
            async function getSystemInfo() {
                const resultDiv = document.getElementById('systemInfo');
                
                try {
                    resultDiv.style.display = 'block';
                    resultDiv.innerHTML = '⏳ Getting system information...';
                    
                    const response = await fetch('/api/v1/health/detailed');
                    const result = await response.json();
                    
                    if (response.ok) {
                        resultDiv.innerHTML = `
                            <strong>Status:</strong> ${result.status}<br>
                            <strong>Version:</strong> ${result.version}<br>
                            <strong>Timestamp:</strong> ${result.timestamp}<br><br>
                            <strong>Services:</strong><br>
                            <ul>
                                <li>Vector Store: ${result.services.vector_store.status}</li>
                                <li>Embedding Service: ${result.services.embedding_service.status}</li>
                                <li>LLM Service: ${result.services.llm_service.status}</li>
                            </ul>
                            <strong>Configuration:</strong><br>
                            <ul>
                                <li>Chunk Size: ${result.configuration.chunk_size}</li>
                                <li>Max File Size: ${result.configuration.max_file_size_mb} MB</li>
                                <li>Top K Results: ${result.configuration.top_k_results}</li>
                                <li>Similarity Threshold: ${result.configuration.similarity_threshold}</li>
                            </ul>
                        `;
                    } else {
                        resultDiv.innerHTML = `❌ Error: ${result.detail}`;
                    }
                } catch (error) {
                    resultDiv.innerHTML = `❌ Error: ${error.message}`;
                }
            }
        </script>
    </body>
    </html>
    """


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    ) 