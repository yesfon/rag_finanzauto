import os
from datasets import load_dataset

# --- Configuración ---
DATASET_NAME = "clarin-knext/fiqa-pl"
RAW_DATA_DIR = "evaluation/raw_data"
NUM_SAMPLES = 100

def main():
    """Descarga el dataset FiQA desde Hugging Face y lo guarda localmente."""
    print(f"--- Iniciando descarga del dataset {DATASET_NAME} ---")

    os.makedirs(RAW_DATA_DIR, exist_ok=True)
    
    try:
        # Descargar las dos partes del dataset
        print("Descargando el corpus (documentos)...")
        corpus = load_dataset(DATASET_NAME, 'corpus', split='corpus')
        
        print("Descargando las preguntas y mapeos (queries)...")
        queries_with_mapping = load_dataset(DATASET_NAME, 'queries', split='queries')
        
        # --- DEBUG: Imprimir información del dataset ---
        print("\n--- INICIO DE DEBUG ---")
        print("\nColumnas del Corpus:", corpus.column_names)
        print("Ejemplo del Corpus:", corpus[0])
        print("\nColumnas de Queries/Mapeo:", queries_with_mapping.column_names)
        print("Ejemplo de Query/Mapeo:", queries_with_mapping[0])
        print("--- FIN DE DEBUG ---\n")
        # --- Fin del DEBUG ---

        # Tomar una muestra para la evaluación
        print(f"Tomando una muestra de {NUM_SAMPLES} preguntas...")
        queries_sample = queries_with_mapping.select(range(NUM_SAMPLES))
        
        # Guardar los archivos
        corpus.to_json(os.path.join(RAW_DATA_DIR, 'corpus.json'), orient="records", lines=True)
        queries_sample.to_json(os.path.join(RAW_DATA_DIR, 'queries_sample.json'), orient="records", lines=True)

        print(f"\n✅ Dataset descargado y guardado en '{RAW_DATA_DIR}'")
        print("-------------------------------------------------")

    except Exception as e:
        print(f"❌ Error durante la descarga del dataset: {e}")

if __name__ == "__main__":
    main() 