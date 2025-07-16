#!/usr/bin/env python3
"""
Script para ejecutar todas las evaluaciones del sistema RAG de manera automatizada.
Incluye evaluación básica, avanzada y generación de reportes.
"""

import os
import sys
import subprocess
import time
from pathlib import Path
from typing import List, Dict, Any

def run_command(command: str, description: str) -> bool:
    """Ejecuta un comando y maneja errores."""
    print(f"\n🔄 {description}")
    print(f"Comando: {command}")
    print("-" * 50)
    
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            capture_output=True, 
            text=True, 
            cwd=Path(__file__).parent
        )
        
        if result.returncode == 0:
            print(f"✅ {description} completado exitosamente")
            if result.stdout:
                print("Salida:", result.stdout)
            return True
        else:
            print(f"❌ Error en {description}")
            print("Error:", result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Excepción en {description}: {e}")
        return False

def check_prerequisites() -> bool:
    """Verifica que los prerrequisitos estén cumplidos."""
    print("🔍 Verificando prerrequisitos...")
    
    # Verificar que el servidor RAG esté ejecutándose
    try:
        import requests
        response = requests.get("http://localhost:8000/api/v1/health/", timeout=5)
        if response.status_code == 200:
            print("Servidor RAG esta ejecutandose")
        else:
            print("Servidor RAG no responde correctamente")
            return False
    except Exception as e:
        print(f"No se puede conectar al servidor RAG: {e}")
        print("Asegurate de que el servidor este ejecutandose en http://localhost:8000")
        return False
    
    # Verificar archivos de datos
    data_files = [
        "evaluation/raw_data/corpus.json",
        "evaluation/raw_data/queries_sample.json"
    ]
    
    for file_path in data_files:
        if not os.path.exists(file_path):
            print(f"Archivo de datos no encontrado: {file_path}")
            return False
    
    print("Todos los prerrequisitos cumplidos")
    return True

def run_basic_evaluation() -> bool:
    """Ejecuta la evaluación básica."""
    return run_command(
        "python evaluate.py",
        "Ejecutando evaluación básica"
    )

def run_advanced_evaluation() -> bool:
    """Ejecuta la evaluación avanzada con bootstraping."""
    return run_command(
        "python evaluate_advanced.py",
        "Ejecutando evaluación avanzada con bootstraping"
    )

def generate_basic_report() -> bool:
    """Genera el reporte básico."""
    return run_command(
        "python visualize_metrics.py",
        "Generando reporte básico de métricas"
    )

def generate_advanced_report() -> bool:
    """Genera el reporte avanzado."""
    return run_command(
        "python visualize_advanced_metrics.py",
        "Generando reporte avanzado con intervalos de confianza"
    )

def print_summary(results: Dict[str, bool]):
    """Imprime un resumen de los resultados."""
    print("\n" + "="*60)
    print("RESUMEN DE EVALUACIONES")
    print("="*60)
    
    for step, success in results.items():
        status = "EXITOSO" if success else "FALLIDO"
        print(f"{step}: {status}")
    
    successful_steps = sum(results.values())
    total_steps = len(results)
    
    print(f"\nResultado: {successful_steps}/{total_steps} pasos exitosos")
    
    if successful_steps == total_steps:
        print("Todas las evaluaciones completadas exitosamente!")
        print("\nArchivos generados:")
        print("  - evaluation/fiqa_results.json")
        print("  - evaluation/squad_es_results.json")
        print("  - evaluation/fiqa_advanced_results.json")
        print("  - evaluation/squad_es_advanced_results.json")
        print("  - evaluation/evaluation_report.html")
        print("  - evaluation/advanced_evaluation_report.html")
    else:
        print("Algunas evaluaciones fallaron. Revisa los errores arriba.")

def main():
    """Función principal para ejecutar todas las evaluaciones."""
    print("Iniciando evaluacion completa del sistema RAG")
    print("="*60)
    
    # Verificar prerrequisitos
    if not check_prerequisites():
        print("Error: Los prerrequisitos no se cumplen. Abortando.")
        sys.exit(1)
    
    # Lista de pasos a ejecutar
    steps = [
        ("Evaluación Básica", run_basic_evaluation),
        ("Evaluación Avanzada", run_advanced_evaluation),
        ("Reporte Básico", generate_basic_report),
        ("Reporte Avanzado", generate_advanced_report)
    ]
    
    results = {}
    
    # Ejecutar cada paso
    for step_name, step_function in steps:
        success = step_function()
        results[step_name] = success
        
        if not success:
            print(f"Advertencia: El paso '{step_name}' fallo, pero continuando con los siguientes...")
    
    # Imprimir resumen
    print_summary(results)
    
    # Sugerir próximos pasos
    print("\nProximos pasos sugeridos:")
    print("1. Revisar los reportes HTML generados")
    print("2. Analizar los intervalos de confianza")
    print("3. Comparar metricas entre datasets")
    print("4. Ajustar parametros del sistema segun los resultados")

if __name__ == "__main__":
    main() 