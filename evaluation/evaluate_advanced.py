import os
import json
import time
import requests
import numpy as np
import pandas as pd
from dotenv import load_dotenv
from rouge_score import rouge_scorer
import nltk
from nltk.translate.bleu_score import sentence_bleu
from tqdm import tqdm
from typing import List, Dict, Any, Tuple
import scipy.stats as stats
from sklearn.metrics import precision_score, recall_score, f1_score
import warnings
warnings.filterwarnings('ignore')

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

class AdvancedRAGEvaluator:
    """Evaluador avanzado de RAG con bootstraping y métricas adicionales."""
    
    def __init__(self, api_base_url: str):
        self.api_base_url = api_base_url
        self.rouge_scorer = rouge_scorer.RougeScorer(['rouge1', 'rouge2', 'rougeL'], use_stemmer=True)
        
    def reset_rag_system(self):
        """Limpia la base de datos del sistema RAG."""
        print("Limpiando la base de datos...")
        try:
            requests.post(f"{self.api_base_url}/documents/reset").raise_for_status()
        except requests.RequestException as e:
            print(f"Error limpiando base de datos: {e}")
    
    def upload_document_from_text(self, text: str, doc_id: str) -> str:
        """Sube un documento de texto al sistema RAG."""
        files = {'file': (f"{doc_id}.txt", text, 'text/plain')}
        response = requests.post(f"{self.api_base_url}/documents/upload", files=files)
        response.raise_for_status()
        return response.json().get('document_id')
    
    def run_query(self, question: str, top_k: int = 10) -> Dict[str, Any]:
        """Ejecuta una consulta en el sistema RAG."""
        payload = {"query": question, "top_k": top_k}
        response = requests.post(f"{self.api_base_url}/query/", json=payload)
        response.raise_for_status()
        return response.json()
    
    def get_embedding(self, text: str) -> List[float]:
        """Obtiene el embedding de un texto."""
        try:
            response = requests.post(f"{self.api_base_url}/embeddings/generate", json={"text": text})
            response.raise_for_status()
            return response.json().get("embedding", [])
        except requests.RequestException:
            return []
    
    def calculate_advanced_metrics(self, generated_answer: str, ideal_answer: str, question: str) -> Dict[str, float]:
        """Calcula métricas avanzadas de calidad de respuesta."""
        # Tokenización
        ideal_tokens = [nltk.word_tokenize(ideal_answer.lower())]
        generated_tokens = nltk.word_tokenize(generated_answer.lower())
        
        # ROUGE Scores
        rouge_scores = self.rouge_scorer.score(ideal_answer, generated_answer)
        rouge_1 = rouge_scores['rouge1'].fmeasure
        rouge_2 = rouge_scores['rouge2'].fmeasure
        rouge_l = rouge_scores['rougeL'].fmeasure
        
        # BLEU Score
        bleu_score = sentence_bleu(ideal_tokens, generated_tokens, weights=(0.25, 0.25, 0.25, 0.25))
        
        # Coherencia semántica
        q_embedding = np.array(self.get_embedding(question))
        a_embedding = np.array(self.get_embedding(generated_answer))
        
        semantic_coherence = 0.0
        if len(q_embedding) > 0 and len(a_embedding) > 0:
            semantic_coherence = np.dot(q_embedding, a_embedding) / (np.linalg.norm(q_embedding) * np.linalg.norm(a_embedding))
        
        # Longitud de respuesta
        answer_length = len(generated_answer.split())
        ideal_length = len(ideal_answer.split())
        length_ratio = answer_length / max(ideal_length, 1)
        
        # Exactitud de palabras clave
        ideal_words = set(ideal_answer.lower().split())
        generated_words = set(generated_answer.lower().split())
        keyword_precision = len(ideal_words.intersection(generated_words)) / max(len(generated_words), 1)
        keyword_recall = len(ideal_words.intersection(generated_words)) / max(len(ideal_words), 1)
        keyword_f1 = 2 * (keyword_precision * keyword_recall) / max(keyword_precision + keyword_recall, 1e-8)
        
        return {
            "rouge_1": rouge_1,
            "rouge_2": rouge_2,
            "rouge_l": rouge_l,
            "bleu": bleu_score,
            "semantic_coherence": float(semantic_coherence),
            "length_ratio": length_ratio,
            "keyword_precision": keyword_precision,
            "keyword_recall": keyword_recall,
            "keyword_f1": keyword_f1
        }
    
    def calculate_retrieval_metrics(self, retrieved_doc_ids: List[str], expected_doc_id: str, k_values: List[int] = [1, 3, 5, 10]) -> Dict[str, float]:
        """Calcula métricas de recuperación para diferentes valores de k."""
        metrics = {}
        for k in k_values:
            hit_rate = 1.0 if expected_doc_id in retrieved_doc_ids[:k] else 0.0
            metrics[f"hit_rate_at_{k}"] = hit_rate
        return metrics
    
    def bootstrap_confidence_intervals(self, metrics_list: List[Dict[str, float]], confidence_level: float = 0.95, n_bootstrap: int = 1000) -> Dict[str, Dict[str, float]]:
        """Calcula intervalos de confianza usando bootstraping."""
        if not metrics_list:
            return {}
        
        metric_names = metrics_list[0].keys()
        bootstrap_results = {}
        
        for metric_name in metric_names:
            values = [result[metric_name] for result in metrics_list if metric_name in result]
            if not values:
                continue
                
            bootstrap_samples = []
            for _ in range(n_bootstrap):
                sample = np.random.choice(values, size=len(values), replace=True)
                bootstrap_samples.append(np.mean(sample))
            
            bootstrap_samples = np.array(bootstrap_samples)
            lower_percentile = (1 - confidence_level) / 2 * 100
            upper_percentile = (1 + confidence_level) / 2 * 100
            
            bootstrap_results[metric_name] = {
                "mean": float(np.mean(values)),
                "std": float(np.std(values)),
                "ci_lower": float(np.percentile(bootstrap_samples, lower_percentile)),
                "ci_upper": float(np.percentile(bootstrap_samples, upper_percentile)),
                "median": float(np.median(values)),
                "min": float(np.min(values)),
                "max": float(np.max(values))
            }
        
        return bootstrap_results
    
    def evaluate_dataset(self, corpus_path: str, queries_path: str, dataset_name: str) -> Dict[str, Any]:
        """Evalúa un dataset completo con métricas avanzadas y bootstraping."""
        print(f"--- Evaluacion Avanzada RAG | Dataset: {dataset_name.upper()} ---")
        
        # 1. Cargar datos
        with open(corpus_path, 'r', encoding='utf-8') as f:
            corpus = [json.loads(line) for line in f]
        with open(queries_path, 'r', encoding='utf-8') as f:
            qa_sample = [json.loads(line) for line in f]
        corpus_map = {item['_id']: item['text'] for item in corpus}
        
        # 2. Preparar entorno
        self.reset_rag_system()
        print(f"Subiendo {len(corpus)} documentos...")
        api_doc_id_map = {
            doc['_id']: self.upload_document_from_text(doc['text'], doc['_id'])
            for doc in tqdm(corpus, desc="Subiendo documentos")
        }
        print("Subida completa. Esperando procesamiento...")
        time.sleep(15)
        
        # 3. Construir dataset de evaluación
        eval_dataset = [
            {
                "question": qa['text'], 
                "ideal_answer": corpus_map[qa['_id']], 
                "expected_doc_id": api_doc_id_map.get(qa['_id'])
            }
            for qa in qa_sample if qa['_id'] in corpus_map
        ]
        
        # 4. Ejecutar evaluación
        detailed_results = []
        for item in tqdm(eval_dataset, desc="Evaluando consultas"):
            try:
                api_response = self.run_query(item['question'])
                retrieved_chunks = api_response.get('retrieved_chunks', [])
                retrieved_doc_ids = list(set(chunk['document_id'] for chunk in retrieved_chunks))
                
                # Métricas de calidad de respuesta
                quality_metrics = self.calculate_advanced_metrics(
                    api_response.get('answer', ''), 
                    item['ideal_answer'], 
                    item['question']
                )
                
                # Métricas de recuperación
                retrieval_metrics = self.calculate_retrieval_metrics(
                    retrieved_doc_ids, 
                    item['expected_doc_id']
                )
                
                detailed_results.append({
                    "question": item['question'],
                    "generated_answer": api_response.get('answer', ''),
                    "ideal_answer": item['ideal_answer'],
                    "metrics": {
                        **quality_metrics,
                        **retrieval_metrics
                    },
                    "retrieval_info": {
                        "expected_doc_id": item['expected_doc_id'],
                        "retrieved_doc_ids": retrieved_doc_ids,
                        "num_retrieved": len(retrieved_doc_ids),
                        "processing_time": api_response.get('processing_time', 0)
                    }
                })
            except Exception as e:
                detailed_results.append({
                    "question": item['question'], 
                    "error": str(e)
                })
        
        # 5. Calcular estadísticas con bootstraping
        valid_results = [r for r in detailed_results if 'error' not in r]
        
        if not valid_results:
                    print("No hay resultados validos para analizar")
        return {}
        
        # Métricas de calidad
        quality_metrics_list = [r['metrics'] for r in valid_results]
        bootstrap_quality = self.bootstrap_confidence_intervals(quality_metrics_list)
        
        # Métricas agregadas
        avg_metrics = {}
        for metric_name in quality_metrics_list[0].keys():
            values = [result[metric_name] for result in quality_metrics_list]
            avg_metrics[metric_name] = float(np.mean(values))
        
        # Estadísticas de recuperación
        retrieval_stats = {
            "total_questions": len(valid_results),
            "successful_queries": len([r for r in valid_results if r['retrieval_info']['num_retrieved'] > 0]),
            "avg_processing_time": float(np.mean([r['retrieval_info']['processing_time'] for r in valid_results])),
            "avg_retrieved_chunks": float(np.mean([r['retrieval_info']['num_retrieved'] for r in valid_results]))
        }
        
        # 6. Generar reporte completo
        report = {
            "dataset": dataset_name,
            "evaluation_config": {
                "num_corpus_docs": len(corpus),
                "num_questions": len(valid_results),
                "top_k_retrieval": 10,
                "temperature": 0.0,
                "bootstrap_samples": 1000,
                "confidence_level": 0.95
            },
            "summary_statistics": {
                "average_metrics": avg_metrics,
                "retrieval_statistics": retrieval_stats
            },
            "bootstrap_confidence_intervals": bootstrap_quality,
            "detailed_results": detailed_results
        }
        
        return report
    
    def save_results(self, report: Dict[str, Any], output_path: str):
        """Guarda los resultados en formato JSON."""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=4, ensure_ascii=False)
        print(f"Resultados guardados en: {output_path}")
    
    def print_summary(self, report: Dict[str, Any]):
        """Imprime un resumen de los resultados."""
        if not report:
            return
        
        print("\n" + "="*60)
        print("RESUMEN DE EVALUACION AVANZADA")
        print("="*60)
        
        print(f"Dataset: {report['dataset']}")
        print(f"Preguntas evaluadas: {report['summary_statistics']['retrieval_statistics']['total_questions']}")
        print(f"Consultas exitosas: {report['summary_statistics']['retrieval_statistics']['successful_queries']}")
        print(f"Tiempo promedio de procesamiento: {report['summary_statistics']['retrieval_statistics']['avg_processing_time']:.3f}s")
        
        print("\nMETRICAS PROMEDIO:")
        for metric, value in report['summary_statistics']['average_metrics'].items():
            print(f"  {metric}: {value:.4f}")
        
        print("\nINTERVALOS DE CONFIANZA (95%):")
        for metric, stats in report['bootstrap_confidence_intervals'].items():
            print(f"  {metric}: {stats['mean']:.4f} [{stats['ci_lower']:.4f}, {stats['ci_upper']:.4f}]")
        
        print("="*60)

def detect_dataset_name(corpus_path: str) -> str:
    """Detecta el nombre del dataset basado en la estructura del corpus."""
    try:
        with open(corpus_path, 'r', encoding='utf-8') as f:
            first_line = f.readline()
            if not first_line:
                return "Unknown"
            data = json.loads(first_line)
            return "squad_es" if 'title' in data else "fiqa"
    except (FileNotFoundError, json.JSONDecodeError):
        return "fiqa"

def main():
    """Función principal para ejecutar la evaluación avanzada."""
    dataset_name = detect_dataset_name(CORPUS_PATH)
    RESULTS_PATH = f"evaluation/{dataset_name}_advanced_results.json"
    
    # Crear evaluador
    evaluator = AdvancedRAGEvaluator(API_BASE_URL)
    
    # Ejecutar evaluación
    report = evaluator.evaluate_dataset(CORPUS_PATH, QUERIES_SAMPLE_PATH, dataset_name)
    
    if report:
        # Guardar resultados
        evaluator.save_results(report, RESULTS_PATH)
        
        # Imprimir resumen
        evaluator.print_summary(report)
        
        print(f"\nEvaluacion completada exitosamente!")
        print(f"Resultados detallados guardados en: {RESULTS_PATH}")
    else:
        print("Error: No se pudo completar la evaluacion")

if __name__ == "__main__":
    main() 