import os
import json
import random
from datasets import load_dataset
from tqdm import tqdm

# Añadimos el path de la app para que encuentre los módulos
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# --- Configuración ---
RAW_DATA_DIR = "evaluation/raw_data"
NUM_SAMPLES = 50  # Número de muestras a tomar del dataset
TARGET_CORPUS_PATH = os.path.join(RAW_DATA_DIR, 'corpus.json')
TARGET_QUERIES_PATH = os.path.join(RAW_DATA_DIR, 'queries_sample.json')
DATASET_NAME = "squad_es"
DATASET_VERSION = "v1.1.0"
DATASET_SPLIT = "validation"

def main():
    """
    Descarga el dataset SQuAD-es, toma una muestra y lo formatea
    en un corpus de documentos y un conjunto de preguntas (con respuestas) para la evaluación RAG.
    """
    print(f"--- Iniciando la preparación del dataset {DATASET_NAME} ---")

    if not os.path.exists(RAW_DATA_DIR):
        os.makedirs(RAW_DATA_DIR)

    print(f"Descargando el dataset '{DATASET_NAME}' (split: {DATASET_SPLIT}, version: {DATASET_VERSION})...")
    dataset = load_dataset(DATASET_NAME, DATASET_VERSION, split=DATASET_SPLIT)
    
    sample_indices = random.sample(range(len(dataset)), NUM_SAMPLES)
    sampled_data = dataset.select(sample_indices)

    corpus = {}
    queries = []

    for item in tqdm(sampled_data, desc="Procesando SQuAD-es"):
        doc_id = item['id']
        answer = item['answers']['text'][0] if item['answers']['text'] else None
        
        if doc_id not in corpus:
            corpus[doc_id] = {"_id": doc_id, "title": item['title'], "text": item['context']}
        
        if answer:
            queries.append({"_id": doc_id, "text": item['question'], "answer": answer})

    with open(TARGET_CORPUS_PATH, 'w', encoding='utf-8') as f:
        for doc in corpus.values():
            f.write(json.dumps(doc, ensure_ascii=False) + '\n')

    with open(TARGET_QUERIES_PATH, 'w', encoding='utf-8') as f:
        for query in queries:
            f.write(json.dumps(query, ensure_ascii=False) + '\n')
            
    print("\n--- Preparación del dataset completada ---")
    print(f"Corpus: {len(corpus)} documentos.")
    print(f"Queries: {len(queries)} preguntas.")

if __name__ == "__main__":
    main()