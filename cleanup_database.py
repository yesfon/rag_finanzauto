#!/usr/bin/env python3
"""
Script para limpiar la base de datos vectorial de RAG FinanzAuto.
"""

import os
import sys
import shutil
import argparse
from pathlib import Path

def cleanup_chroma_directory():
    """Limpiar directorio de ChromaDB directamente."""
    chroma_dir = Path("./data/chroma_db")
    
    if chroma_dir.exists():
        try:
            shutil.rmtree(chroma_dir)
            print(f"✅ Directorio {chroma_dir} eliminado exitosamente")
            return True
        except Exception as e:
            print(f"❌ Error al eliminar directorio {chroma_dir}: {e}")
            return False
    else:
        print(f"ℹ️ Directorio {chroma_dir} no existe")
        return True

def cleanup_upload_directory():
    """Limpiar directorio de uploads."""
    upload_dir = Path("./data/uploads")
    
    if upload_dir.exists():
        try:
            shutil.rmtree(upload_dir)
            print(f"✅ Directorio {upload_dir} eliminado exitosamente")
            return True
        except Exception as e:
            print(f"❌ Error al eliminar directorio {upload_dir}: {e}")
            return False
    else:
        print(f"ℹ️ Directorio {upload_dir} no existe")
        return True

def cleanup_logs():
    """Limpiar logs."""
    logs_dir = Path("./logs")
    
    if logs_dir.exists():
        try:
            for log_file in logs_dir.glob("*.log"):
                log_file.unlink()
            print(f"✅ Logs limpiados exitosamente")
            return True
        except Exception as e:
            print(f"❌ Error al limpiar logs: {e}")
            return False
    else:
        print(f"ℹ️ Directorio {logs_dir} no existe")
        return True

def main():
    """Función principal."""
    parser = argparse.ArgumentParser(description="Limpiar base de datos RAG FinanzAuto")
    parser.add_argument("--all", action="store_true", help="Limpiar todo (base de datos, uploads, logs)")
    parser.add_argument("--db-only", action="store_true", help="Limpiar solo la base de datos vectorial")
    parser.add_argument("--uploads", action="store_true", help="Limpiar directorio de uploads")
    parser.add_argument("--logs", action="store_true", help="Limpiar logs")
    parser.add_argument("--force", action="store_true", help="Forzar limpieza sin confirmación")
    
    args = parser.parse_args()
    
    # Verificar que estamos en el directorio correcto
    if not os.path.exists("app/main.py"):
        print("❌ Error: No se encuentra app/main.py")
        print("Asegúrate de ejecutar este script desde el directorio raíz del proyecto")
        sys.exit(1)
    
    print("🧹 RAG FinanzAuto - Limpieza de Base de Datos")
    print("=" * 50)
    
    # Determinar qué limpiar
    clean_db = args.all or args.db_only or (not any([args.uploads, args.logs]))
    clean_uploads = args.all or args.uploads
    clean_logs = args.all or args.logs
    
    # Mostrar qué se va a limpiar
    actions = []
    if clean_db:
        actions.append("Base de datos vectorial (ChromaDB)")
    if clean_uploads:
        actions.append("Directorio de uploads")
    if clean_logs:
        actions.append("Logs")
    
    if not actions:
        print("❌ No se especificaron acciones de limpieza")
        sys.exit(1)
    
    print("Se procederá a limpiar:")
    for action in actions:
        print(f"  - {action}")
    
    # Confirmar si no es forzado
    if not args.force:
        confirm = input("\n¿Continuar con la limpieza? (s/N): ").lower()
        if confirm != 's':
            print("❌ Limpieza cancelada")
            sys.exit(0)
    
    # Ejecutar limpieza
    success = True
    
    if clean_db:
        print("\n🗑️ Limpiando base de datos vectorial...")
        if not cleanup_chroma_directory():
            success = False
    
    if clean_uploads:
        print("\n🗑️ Limpiando directorio de uploads...")
        if not cleanup_upload_directory():
            success = False
    
    if clean_logs:
        print("\n🗑️ Limpiando logs...")
        if not cleanup_logs():
            success = False
    
    # Resultado final
    if success:
        print("\n✅ Limpieza completada exitosamente")
        print("\nPuedes iniciar la aplicación con:")
        print("  python cleanup_database.py --db-only")
        print("  python cleanup_database.py --all --force")
        print("\nPara iniciar la aplicación principal:")
        print("  python -m uvicorn app.main:app --reload")
    else:
        print("\n⚠️ Limpieza completada con algunos errores")
        sys.exit(1)

if __name__ == "__main__":
    main() 