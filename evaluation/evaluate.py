import os
import json
import time
import requests
from dotenv import load_dotenv
from rouge_score import rouge_scorer
import nltk
from nltk.translate.bleu_score import sentence_bleu
# Se elimina la importación de bert_score
from tqdm import tqdm
import numpy as np

# --- Configuración ---
load_dotenv()
API_BASE_URL = os.getenv("API_URL", "http://localhost:8000/api/v1")
RAW_DATA_DIR = "evaluation/raw_data"
CORPUS_PATH = os.path.join(RAW_DATA_DIR, 'corpus.json')
QUERIES_SAMPLE_PATH = os.path.join(RAW_DATA_DIR, 'queries_sample.json')

# --- Descarga de NLTK ---
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    print("Descargando el tokenizador 'punkt' de NLTK...")
    nltk.download('punkt', quiet=True)

# --- Funciones de Ayuda ---
def detect_dataset_name(corpus_path):
    """Detecta el nombre del dataset basado en la estructura del corpus."""
    try:
        with open(corpus_path, 'r', encoding='utf-8') as f:
            first_line = f.readline()
            if not first_line: return "Unknown"
            data = json.loads(first_line)
            return "squad_es" if 'title' in data else "fiqa"
    except (FileNotFoundError, json.JSONDecodeError):
        return "fiqa"

# --- Funciones de Interacción con la API ---
def reset_rag_system():
    print("Limpiando la base de datos...")
    # Este endpoint debería existir en tu API para limpiar la DB
    # Asumiendo que está en /documents/reset
    requests.post(f"{API_BASE_URL}/documents/reset").raise_for_status()

def upload_document_from_text(text, doc_id):
    files = {'file': (f"{doc_id}.txt", text, 'text/plain')}
    response = requests.post(f"{API_BASE_URL}/documents/upload", files=files)
    response.raise_for_status()
    return response.json().get('document_id')

def run_query(question):
    payload = {"query": question, "top_k": 10}
    response = requests.post(f"{API_BASE_URL}/query/", json=payload)
    response.raise_for_status()
    return response.json()

def get_embedding(text):
    """Obtiene el embedding de un texto a través de un supuesto endpoint."""
    try:
        response = requests.post(f"{API_BASE_URL}/embeddings/generate", json={"text": text})
        response.raise_for_status()
        return response.json().get("embedding")
    except requests.RequestException:
        return None # Devolver None si hay error

# --- Funciones de Evaluación ---
def calculate_metrics(generated_answer, ideal_answer, question):
    """Calcula todas las métricas de calidad de la respuesta."""
    ideal_tokens = [nltk.word_tokenize(ideal_answer.lower())]
    generated_tokens = nltk.word_tokenize(generated_answer.lower())
    
    rouge = rouge_scorer.RougeScorer(['rougeL'], use_stemmer=True).score(ideal_answer, generated_answer)
    rouge_l = rouge['rougeL'].fmeasure
    
    bleu_score = sentence_bleu(ideal_tokens, generated_tokens, weights=(0.25, 0.25, 0.25, 0.25))

    # Se elimina el cálculo de BERTScore

    q_embedding = np.array(get_embedding(question) or [])
    a_embedding = np.array(get_embedding(generated_answer) or [])
    
    semantic_coherence = 0.0
    if q_embedding.any() and a_embedding.any():
        semantic_coherence = np.dot(q_embedding, a_embedding) / (np.linalg.norm(q_embedding) * np.linalg.norm(a_embedding))

    return {
        "rouge_l": rouge_l,
        "bleu": bleu_score,
        # "bert_score" eliminado
        "semantic_coherence": float(semantic_coherence)
    }

def calculate_hit_rate_at_k(retrieved_doc_ids, expected_doc_id, k=5):
    return 1.0 if expected_doc_id in retrieved_doc_ids[:k] else 0.0

# --- Script Principal ---
def main():
    dataset_name = detect_dataset_name(CORPUS_PATH)
    # El nombre del archivo de resultados ya no necesita el motor
    RESULTS_PATH = f"evaluation/{dataset_name}_full_metrics_results.json"
    
    print(f"--- Evaluación Completa RAG | Dataset: {dataset_name.upper()} ---")

    # 1. Cargar datos
    with open(CORPUS_PATH, 'r', encoding='utf-8') as f:
        corpus = [json.loads(line) for line in f]
    with open(QUERIES_SAMPLE_PATH, 'r', encoding='utf-8') as f:
        qa_sample = [json.loads(line) for line in f]
    corpus_map = {item['_id']: item['text'] for item in corpus}

    # 2. Preparar entorno
    reset_rag_system()
    print(f"Subiendo {len(corpus)} documentos...")
    api_doc_id_map = {
        fiqa_doc['_id']: upload_document_from_text(fiqa_doc['text'], fiqa_doc['_id'])
        for fiqa_doc in tqdm(corpus, desc="Subiendo documentos")
    }
    print("Subida completa. Esperando procesamiento...")
    time.sleep(15)

    # 3. Construir dataset de evaluación
    eval_dataset = [
        {"question": qa['text'], "ideal_answer": corpus_map[qa['_id']], "expected_doc_id": api_doc_id_map.get(qa['_id'])}
        for qa in qa_sample if qa['_id'] in corpus_map
    ]

    # 4. Ejecutar evaluación
    detailed_results = []
    for item in tqdm(eval_dataset, desc=f"Evaluando con motor original"):
        try:
            api_response = run_query(item['question']) # Llamada simplificada
            retrieved_chunks = api_response.get('retrieved_chunks', [])
            retrieved_doc_ids = list(set(chunk['document_id'] for chunk in retrieved_chunks))
            
            quality_metrics = calculate_metrics(api_response.get('answer', ''), item['ideal_answer'], item['question'])
            
            detailed_results.append({
                "question": item['question'],
                "generated_answer": api_response.get('answer', ''),
                "metrics": {
                    "hit_rate_at_5": calculate_hit_rate_at_k(retrieved_doc_ids, item['expected_doc_id']),
                    **quality_metrics
                },
                "retrieval_info": {
                    "expected_doc_id": item['expected_doc_id'],
                    "retrieved_doc_ids": retrieved_doc_ids,
                    "is_hit": item['expected_doc_id'] in retrieved_doc_ids[:5]
                }
            })
        except Exception as e:
            detailed_results.append({"question": item['question'], "error": str(e)})

    # 5. Calcular promedios y guardar
    avg_metrics = {key: 0.0 for key in detailed_results[0]['metrics'].keys()}
    valid_results = [r for r in detailed_results if 'error' not in r]
    for key in avg_metrics:
        avg_metrics[key] = sum(r['metrics'][key] for r in valid_results) / len(valid_results)

    summary = {
        "engine": "original", # Hardcodeado a original
        "dataset": dataset_name,
        "num_questions": len(valid_results),
        "average_metrics": avg_metrics,
    }

    with open(RESULTS_PATH, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=4, ensure_ascii=False)
    
    print("\n--- Evaluación Completada ---")
    print(json.dumps(summary, indent=4))
    print(f"Resultados guardados en: {RESULTS_PATH}")

if __name__ == "__main__":
    # La ejecución vuelve a ser directa, sin argumentos
    main() 