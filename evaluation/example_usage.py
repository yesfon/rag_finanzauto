#!/usr/bin/env python3
"""
Ejemplo de uso de las funcionalidades de evaluación avanzada del sistema RAG.
Este script demuestra cómo ejecutar evaluaciones y analizar resultados.
"""

import json
import os
import sys
from pathlib import Path

def print_header(title: str):
    """Imprime un encabezado formateado."""
    print("\n" + "="*60)
    print(f"📋 {title}")
    print("="*60)

def print_section(title: str):
    """Imprime un título de sección."""
    print(f"\n🔹 {title}")
    print("-" * 40)

def load_results(file_path: str) -> dict:
    """Carga resultados desde un archivo JSON."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ Archivo no encontrado: {file_path}")
        return {}
    except json.JSONDecodeError:
        print(f"❌ Error al parsear JSON: {file_path}")
        return {}

def analyze_basic_results():
    """Analiza los resultados básicos de evaluación."""
    print_section("Análisis de Resultados Básicos")
    
    # Cargar resultados de FIQA
    fiqa_results = load_results("fiqa_results.json")
    if fiqa_results:
        print("📊 Resultados FIQA:")
        print(f"  - Dataset: {fiqa_results.get('dataset', 'N/A')}")
        print(f"  - Preguntas evaluadas: {fiqa_results.get('evaluation_config', {}).get('num_questions', 0)}")
        
        avg_metrics = fiqa_results.get('average_metrics', {})
        print("  - Métricas promedio:")
        for metric, value in avg_metrics.items():
            print(f"    * {metric}: {value:.4f}")
    
    # Cargar resultados de SQuAD-ES
    squad_results = load_results("squad_es_results.json")
    if squad_results:
        print("\n📊 Resultados SQuAD-ES:")
        print(f"  - Dataset: {squad_results.get('dataset', 'N/A')}")
        print(f"  - Preguntas evaluadas: {squad_results.get('evaluation_config', {}).get('num_questions', 0)}")
        
        avg_metrics = squad_results.get('average_metrics', {})
        print("  - Métricas promedio:")
        for metric, value in avg_metrics.items():
            print(f"    * {metric}: {value:.4f}")

def analyze_advanced_results():
    """Analiza los resultados avanzados con intervalos de confianza."""
    print_section("Análisis de Resultados Avanzados")
    
    # Cargar resultados avanzados de FIQA
    fiqa_advanced = load_results("fiqa_advanced_results.json")
    if fiqa_advanced:
        print("📊 Resultados Avanzados FIQA:")
        print(f"  - Dataset: {fiqa_advanced.get('dataset', 'N/A')}")
        
        # Mostrar configuración
        config = fiqa_advanced.get('evaluation_config', {})
        print(f"  - Configuración:")
        print(f"    * Temperatura: {config.get('temperature', 'N/A')}")
        print(f"    * Top-K: {config.get('top_k_retrieval', 'N/A')}")
        print(f"    * Bootstrap samples: {config.get('bootstrap_samples', 'N/A')}")
        
        # Mostrar estadísticas de recuperación
        retrieval_stats = fiqa_advanced.get('summary_statistics', {}).get('retrieval_statistics', {})
        print(f"  - Estadísticas de recuperación:")
        print(f"    * Total preguntas: {retrieval_stats.get('total_questions', 0)}")
        print(f"    * Consultas exitosas: {retrieval_stats.get('successful_queries', 0)}")
        print(f"    * Tiempo promedio: {retrieval_stats.get('avg_processing_time', 0):.3f}s")
        
        # Mostrar intervalos de confianza
        bootstrap_intervals = fiqa_advanced.get('bootstrap_confidence_intervals', {})
        if bootstrap_intervals:
            print(f"  - Intervalos de confianza (95%):")
            for metric, stats in bootstrap_intervals.items():
                print(f"    * {metric}: {stats['mean']:.4f} [{stats['ci_lower']:.4f}, {stats['ci_upper']:.4f}]")
    
    # Cargar resultados avanzados de SQuAD-ES
    squad_advanced = load_results("squad_es_advanced_results.json")
    if squad_advanced:
        print("\n📊 Resultados Avanzados SQuAD-ES:")
        print(f"  - Dataset: {squad_advanced.get('dataset', 'N/A')}")
        
        # Mostrar estadísticas de recuperación
        retrieval_stats = squad_advanced.get('summary_statistics', {}).get('retrieval_statistics', {})
        print(f"  - Estadísticas de recuperación:")
        print(f"    * Total preguntas: {retrieval_stats.get('total_questions', 0)}")
        print(f"    * Consultas exitosas: {retrieval_stats.get('successful_queries', 0)}")
        print(f"    * Tiempo promedio: {retrieval_stats.get('avg_processing_time', 0):.3f}s")
        
        # Mostrar intervalos de confianza
        bootstrap_intervals = squad_advanced.get('bootstrap_confidence_intervals', {})
        if bootstrap_intervals:
            print(f"  - Intervalos de confianza (95%):")
            for metric, stats in bootstrap_intervals.items():
                print(f"    * {metric}: {stats['mean']:.4f} [{stats['ci_lower']:.4f}, {stats['ci_upper']:.4f}]")

def compare_datasets():
    """Compara los resultados entre datasets."""
    print_section("Comparación entre Datasets")
    
    # Cargar todos los resultados
    fiqa_basic = load_results("fiqa_results.json")
    squad_basic = load_results("squad_es_results.json")
    fiqa_advanced = load_results("fiqa_advanced_results.json")
    squad_advanced = load_results("squad_es_advanced_results.json")
    
    if fiqa_basic and squad_basic:
        print("📈 Comparación de Hit Rate@5:")
        fiqa_hit_rate = fiqa_basic.get('average_metrics', {}).get('hit_rate_at_5', 0)
        squad_hit_rate = squad_basic.get('average_metrics', {}).get('hit_rate_at_5', 0)
        print(f"  - FIQA: {fiqa_hit_rate:.4f}")
        print(f"  - SQuAD-ES: {squad_hit_rate:.4f}")
        
        if fiqa_hit_rate > squad_hit_rate:
            print(f"  🏆 FIQA tiene mejor rendimiento en recuperación")
        else:
            print(f"  🏆 SQuAD-ES tiene mejor rendimiento en recuperación")
    
    if fiqa_basic and squad_basic:
        print("\n📈 Comparación de ROUGE-L:")
        fiqa_rouge = fiqa_basic.get('average_metrics', {}).get('rouge_l_fmeasure', 0)
        squad_rouge = squad_basic.get('average_metrics', {}).get('rouge_l_fmeasure', 0)
        print(f"  - FIQA: {fiqa_rouge:.4f}")
        print(f"  - SQuAD-ES: {squad_rouge:.4f}")
        
        if fiqa_rouge > squad_rouge:
            print(f"  🏆 FIQA tiene mejor calidad de respuesta")
        else:
            print(f"  🏆 SQuAD-ES tiene mejor calidad de respuesta")

def show_usage_instructions():
    """Muestra las instrucciones de uso."""
    print_section("Instrucciones de Uso")
    
    print("🚀 Para ejecutar evaluaciones:")
    print("1. Asegúrate de que el servidor RAG esté ejecutándose:")
    print("   ./start.sh")
    print()
    print("2. Ejecuta la evaluación completa:")
    print("   python evaluation/run_all_evaluations.py")
    print()
    print("3. O ejecuta evaluaciones individuales:")
    print("   python evaluation/evaluate.py                    # Evaluación básica")
    print("   python evaluation/evaluate_advanced.py           # Evaluación con bootstraping")
    print("   python evaluation/visualize_metrics.py           # Reporte básico")
    print("   python evaluation/visualize_advanced_metrics.py  # Reporte avanzado")
    print()
    print("4. Revisa los archivos generados:")
    print("   - evaluation/*_results.json                     # Resultados JSON")
    print("   - evaluation/evaluation_report.html             # Reporte básico")
    print("   - evaluation/advanced_evaluation_report.html    # Reporte avanzado")

def main():
    """Función principal del ejemplo de uso."""
    print_header("Ejemplo de Uso - Evaluacion Avanzada RAG")
    
    # Cambiar al directorio de evaluación
    evaluation_dir = Path(__file__).parent
    os.chdir(evaluation_dir)
    
    print("📁 Directorio de trabajo:", os.getcwd())
    
    # Mostrar instrucciones
    show_usage_instructions()
    
    # Analizar resultados si existen
    print_section("Análisis de Resultados Existentes")
    
    if any(os.path.exists(f) for f in ["fiqa_results.json", "squad_es_results.json"]):
        analyze_basic_results()
    else:
        print("Advertencia: No se encontraron resultados basicos. Ejecuta primero las evaluaciones.")
    
    if any(os.path.exists(f) for f in ["fiqa_advanced_results.json", "squad_es_advanced_results.json"]):
        analyze_advanced_results()
    else:
        print("Advertencia: No se encontraron resultados avanzados. Ejecuta primero las evaluaciones avanzadas.")
    
    # Comparar datasets
    compare_datasets()
    
    print_header("Resumen")
    print("Este script demuestra como:")
    print("   - Cargar y analizar resultados de evaluacion")
    print("   - Comparar metricas entre datasets")
    print("   - Interpretar intervalos de confianza")
    print("   - Generar reportes visuales")
    print()
    print("Para mas informacion, consulta el README.md")

if __name__ == "__main__":
    main() 