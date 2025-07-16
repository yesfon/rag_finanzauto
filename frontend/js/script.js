document.addEventListener("DOMContentLoaded", () => {
    // API endpoints
    const API_BASE_URL = "http://localhost:8000/api/v1";
    const QUERY_API = `${API_BASE_URL}/query/`;
    const UPLOAD_API = `${API_BASE_URL}/documents/upload`;
    const DOC_LIST_API = `${API_BASE_URL}/documents/list-unique`;
    const DELETE_DOC_API = (id) => `${API_BASE_URL}/documents/${id}`;
    const RESET_DOCS_API = `${API_BASE_URL}/documents/reset`;
    const STATUS_API = `${API_BASE_URL}/health/detailed`;

    // --- Element Selectors ---
    const chatMessages = document.getElementById("chat-messages");
    const chatForm = document.getElementById("chat-form");
    const messageInput = document.getElementById("message-input");
    const uploadForm = document.getElementById("upload-form");
    const fileInput = document.getElementById("file-input");
    const browseBtn = document.getElementById("browse-btn");
    const fileDropArea = document.querySelector(".file-drop-area");
    const fileNameDisplay = document.getElementById("file-name-display");
    const docListContainer = document.getElementById("doc-list-container");
    const statusContainer = document.getElementById("status-container");
    const toastContainer = document.getElementById("toast-container");
    const topKSlider = document.getElementById("top-k-slider");
    const topKValue = document.getElementById("top-k-value");
    const thresholdSlider = document.getElementById("threshold-slider");
    const thresholdValue = document.getElementById("threshold-value");
    const docCountEl = document.getElementById("doc-count");
    const queryCountEl = document.getElementById("query-count");
    const confirmModal = document.getElementById("confirm-modal");
    const modalText = document.getElementById("modal-text");
    const modalConfirmBtn = document.getElementById("modal-confirm-btn");
    const modalCancelBtn = document.getElementById("modal-cancel-btn");
    
    let selectedFile = null;
    let queryCount = 0;
    let resolveConfirm = null;

    // --- Toast Notification Function ---
    const showToast = (message, type = 'info') => {
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.innerHTML = `<i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i> ${message}`;
        toastContainer.appendChild(toast);
        setTimeout(() => toast.remove(), 5000);
    };

    // --- Custom Confirmation Modal ---
    const showConfirmModal = (text) => {
        modalText.textContent = text;
        confirmModal.style.display = 'flex';
        return new Promise((resolve) => {
            resolveConfirm = resolve;
        });
    };

    const hideConfirmModal = () => {
        confirmModal.style.display = 'none';
    };

    modalConfirmBtn.addEventListener('click', () => {
        if (resolveConfirm) resolveConfirm(true);
        hideConfirmModal();
    });

    modalCancelBtn.addEventListener('click', () => {
        if (resolveConfirm) resolveConfirm(false);
        hideConfirmModal();
    });

    // --- Chat Functions ---
    // ... (existing addMessage, createChunksAccordion, etc.)
    const escapeHTML = (str) => {
        const p = document.createElement("p");
        p.appendChild(document.createTextNode(str));
        return p.innerHTML;
    };
    
    const addMessage = (text, sender, chunks = []) => {
        const messageElement = document.createElement("div");
        messageElement.classList.add("message", `${sender}-message`);

        const avatar = document.createElement("div");
        avatar.classList.add("avatar");
        avatar.innerHTML = sender === "user" ? "U" : '<i class="fas fa-robot"></i>';
        
        const contentWrapper = document.createElement("div");
        contentWrapper.classList.add("message-content-wrapper");

        const content = document.createElement("div");
        content.classList.add("message-content");
        content.innerHTML = text;

        contentWrapper.appendChild(content);
        
        if (chunks && chunks.length > 0) {
            contentWrapper.appendChild(createChunksAccordion(chunks));
        }
        
        messageElement.appendChild(avatar);
        messageElement.appendChild(contentWrapper);

        chatMessages.appendChild(messageElement);
        scrollToBottom();
    };

    const createChunksAccordion = (chunks) => {
        const details = document.createElement("details");
        details.className = "source-container";

        const summary = document.createElement("summary");
        summary.innerHTML = `<i class="fas fa-book"></i> Fuentes (${chunks.length})`;
        
        const contentDiv = document.createElement("div");
        contentDiv.className = "source-content";

        chunks.forEach((chunk, i) => {
            const item = document.createElement("div");
            item.className = "source-item";

            // Normalizar el texto: reemplazar saltos de línea y espacios múltiples
            const normalizedContent = chunk.content.replace(/\s+/g, ' ').trim();

            item.innerHTML = `
                <div class="source-header">
                    <strong>Fragmento ${i + 1}</strong>
                    <span class="relevance-score">Relevancia: ${chunk.similarity_score.toFixed(2)}</span>
                </div>
                <p class="source-text">${escapeHTML(normalizedContent)}</p>
            `;
            contentDiv.appendChild(item);
        });

        details.appendChild(summary);
        details.appendChild(contentDiv);
        return details;
    };

    const scrollToBottom = () => {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    };

    const showTypingIndicator = () => {
        const typingIndicator = document.createElement("div");
        typingIndicator.id = "typing-indicator";
        typingIndicator.classList.add("message", "bot-message");
        typingIndicator.innerHTML = `
            <div class="avatar"><i class="fas fa-robot"></i></div>
            <div class="message-content-wrapper">
                <div class="message-content typing-animation">
                    <span></span><span></span><span></span>
                </div>
            </div>
        `;
        chatMessages.appendChild(typingIndicator);
        scrollToBottom();
    };

    const removeTypingIndicator = () => {
        const typingIndicator = document.getElementById("typing-indicator");
        if (typingIndicator) typingIndicator.remove();
    };
    
    const updateQueryCount = () => {
        queryCount++;
        queryCountEl.textContent = queryCount;
    };

    const handleChatSubmit = async (event) => {
        event.preventDefault();
        const userText = messageInput.value.trim();
        if (!userText) return;

        addMessage(userText, "user");
        messageInput.value = "";
        showTypingIndicator();

        try {
            const response = await fetch(QUERY_API, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    query: userText,
                    top_k: parseInt(topKSlider.value, 10),
                    similarity_threshold: parseFloat(thresholdSlider.value)
                }),
            });

            removeTypingIndicator();
            if (!response.ok) throw new Error(`Error: ${response.statusText}`);

            const data = await response.json();
            const botText = data.answer.replace(/\n/g, '<br>');
            const chunks = data.retrieved_chunks || [];
            addMessage(botText, "bot", chunks);
            updateQueryCount();
        } catch (error) {
            removeTypingIndicator();
            console.error("Error fetching query:", error);
            showToast("Error al conectar con el servidor.", 'error');
        }
    };

    // --- Control Panel Functions ---

    const handleFileSelect = (file) => {
        if (file) {
            selectedFile = file;
            fileNameDisplay.textContent = `Archivo: ${file.name}`;
            fileDropArea.classList.add("is-active");
        }
    };

    uploadForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        if (!selectedFile) {
            showToast("Por favor, selecciona un archivo.", 'error');
            return;
        }

        const uploadButton = document.getElementById("upload-btn");
        const originalButtonText = uploadButton.innerHTML;
        uploadButton.disabled = true;
        uploadButton.innerHTML = '<span class="spinner"></span> Subiendo...';

        const formData = new FormData();
        formData.append("file", selectedFile);
        formData.append("title", selectedFile.name);

        const initialDocCount = docListContainer.querySelectorAll('.doc-item').length;

        try {
            const response = await fetch(UPLOAD_API, { method: "POST", body: formData });
            if (!response.ok) throw new Error("Falló la subida del archivo.");
            
            showToast("Archivo recibido, procesando...", 'info');
            
            // Iniciar polling
            pollForDocuments(initialDocCount);

        } catch (error) {
            console.error("Error al subir archivo:", error);
            showToast("Error al subir el archivo.", 'error');
            uploadButton.disabled = false;
            uploadButton.innerHTML = originalButtonText;
        } finally {
            selectedFile = null;
            fileNameDisplay.textContent = "";
            fileDropArea.classList.remove("is-active");
        }
    });

    const pollForDocuments = (initialCount) => {
        const uploadButton = document.getElementById("upload-btn");
        const originalButtonText = "Subir Archivo";
        let attempts = 0;
        const maxAttempts = 15; // 30 segundos de timeout (15 * 2s)

        const interval = setInterval(async () => {
            attempts++;
            if (attempts > maxAttempts) {
                clearInterval(interval);
                showToast("El procesamiento está tardando más de lo esperado. La lista se actualizará pronto.", 'info');
                uploadButton.disabled = false;
                uploadButton.innerHTML = originalButtonText;
                return;
            }

            try {
                const response = await fetch(DOC_LIST_API);
                const data = await response.json();
                const currentCount = data.documents ? data.documents.length : 0;

                if (currentCount > initialCount) {
                    clearInterval(interval);
                    showToast("¡Documento procesado y añadido!", 'success');
                    await fetchDocuments(); // Fetch final para asegurar la UI
                    uploadButton.disabled = false;
                    uploadButton.innerHTML = originalButtonText;
                }
            } catch (error) {
                // Sigue intentando, no muestra error de polling
                console.warn("Polling check failed, retrying...");
            }

        }, 2000);
    };
    
    const fetchDocuments = async () => {
        try {
            const response = await fetch(DOC_LIST_API);
            if (!response.ok) throw new Error("No se pudo obtener la lista de documentos.");
            
            const data = await response.json();
            const docs = data.documents || [];
            docCountEl.textContent = docs.length;
            renderDocuments(docs);
        } catch (error) {
            console.error("Error fetching documents:", error);
            docListContainer.innerHTML = '<p class="empty-list-msg">Error al cargar documentos.</p>';
            docCountEl.textContent = "0";
        }
    };

    const renderDocuments = (docs) => {
        docListContainer.innerHTML = "";
        if (docs.length === 0) {
            docListContainer.innerHTML = '<p class="empty-list-msg">No hay documentos disponibles.</p>';
            return;
        }

        docs.forEach(doc => {
            const docElement = document.createElement("div");
            docElement.className = "doc-item";
            docElement.innerHTML = `
                <span class="doc-name" title="${doc.filename}">${doc.filename}</span>
                <button class="delete-btn" data-id="${doc.document_id}" title="Eliminar documento"><i class="fas fa-trash-alt"></i></button>
            `;
            docListContainer.appendChild(docElement);
        });
    };

    docListContainer.addEventListener("click", async (e) => {
        const deleteButton = e.target.closest(".delete-btn");
        if (deleteButton) {
            const docId = deleteButton.dataset.id;
            const confirmed = await showConfirmModal("¿Estás seguro de que quieres eliminar este documento?");
            if (confirmed) {
                try {
                    const response = await fetch(DELETE_DOC_API(docId), { method: "DELETE" });
                    if (!response.ok) throw new Error("No se pudo eliminar el documento.");
                    
                    showToast("Documento eliminado.", 'info');
                    fetchDocuments();
                } catch (error) {
                    console.error("Error al eliminar:", error);
                    showToast("Error al eliminar el documento.", 'error');
                }
            }
        }
    });
    
    const fetchSystemStatus = async () => {
        try {
            const response = await fetch(STATUS_API);
            if (!response.ok) throw new Error("Fallo al obtener estado.");

            const data = await response.json();
            const services = data.services;
            
            const getStatusClass = (status) => status.toLowerCase() === 'healthy' ? 'healthy' : 'unhealthy';

            statusContainer.innerHTML = `
                <div class="status-item"><strong>Vector Store:</strong> <span class="${getStatusClass(services.vector_store.status)}">${services.vector_store.status}</span></div>
                <div class="status-item"><strong>Embedding:</strong> <span class="${getStatusClass(services.embedding_service.status)}">${services.embedding_service.status}</span></div>
                <div class="status-item"><strong>LLM Service:</strong> <span class="${getStatusClass(services.llm_service.status)}">${services.llm_service.status}</span></div>
            `;
        } catch (error) {
            console.error("Error fetching status:", error);
            statusContainer.innerHTML = '<div class="status-item">No se pudo cargar el estado.</div>';
        }
    };

    const resetAllDocumentsOnLoad = async () => {
        try {
            await fetch(RESET_DOCS_API, { method: "POST" });
            console.log("Repositorio de documentos reseteado al cargar la página.");
        } catch (error) {
            console.error("No se pudo resetear el repositorio de documentos:", error);
        }
    };

    // --- Event Listeners & Initialization ---
    chatForm.addEventListener("submit", handleChatSubmit);
    fileDropArea.addEventListener("click", () => fileInput.click());
    browseBtn.addEventListener("click", () => fileInput.click());
    fileInput.addEventListener("change", () => handleFileSelect(fileInput.files[0]));
    
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        fileDropArea.addEventListener(eventName, e => { e.preventDefault(); e.stopPropagation(); });
    });
    ['dragenter', 'dragover'].forEach(eventName => {
        fileDropArea.addEventListener(eventName, () => fileDropArea.classList.add('is-active'));
    });
    ['dragleave', 'drop'].forEach(eventName => {
        fileDropArea.addEventListener(eventName, () => fileDropArea.classList.remove('is-active'));
    });
    fileDropArea.addEventListener("drop", (e) => handleFileSelect(e.dataTransfer.files[0]));

    messageInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            chatForm.dispatchEvent(new Event('submit', { cancelable: true, bubbles: true }));
        }
    });

    topKSlider.addEventListener("input", (e) => topKValue.textContent = e.target.value);
    thresholdSlider.addEventListener("input", (e) => thresholdValue.textContent = parseFloat(e.target.value).toFixed(2));

    // Initial load
    const initializeApp = async () => {
        await resetAllDocumentsOnLoad();
        addMessage("Hola, soy el asistente inteligente de Finanzauto. ¿En qué puedo ayudarte hoy?", "bot");
        fetchDocuments();
        fetchSystemStatus();
    };

    initializeApp();
}); 