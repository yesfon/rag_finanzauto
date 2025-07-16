#!/bin/bash

# RAG FinanzAuto Setup Script
# Este script configura el entorno de desarrollo para RAG FinanzAuto

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para imprimir mensajes
print_message() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

# Verificar si miniconda está instalado
check_conda() {
    if ! command -v conda &> /dev/null; then
        print_error "Miniconda/Anaconda no está instalado."
        print_message "Por favor instala Miniconda desde: https://docs.conda.io/en/latest/miniconda.html"
        exit 1
    fi
    print_message "Miniconda/Anaconda encontrado ✓"
}

# Verificar si Docker está instalado
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_warning "Docker no está instalado. Algunas funcionalidades no estarán disponibles."
        return 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_warning "Docker Compose no está instalado. Algunas funcionalidades no estarán disponibles."
        return 1
    fi
    
    print_message "Docker y Docker Compose encontrados ✓"
    return 0
}

# Crear entorno conda
setup_conda_env() {
    print_header "Configurando entorno Conda"
    
    # Verificar si el entorno ya existe
    if conda env list | grep -q "rag_finanzauto"; then
        print_warning "El entorno 'rag_finanzauto' ya existe."
        read -p "¿Deseas recrearlo? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            print_message "Eliminando entorno existente..."
            conda env remove -n rag_finanzauto -y
        else
            print_message "Usando entorno existente."
            return 0
        fi
    fi
    
    print_message "Creando entorno conda desde environment.yml..."
    conda env create -f environment.yml
    
    print_message "Entorno conda creado exitosamente ✓"
}

# Configurar variables de entorno
setup_env_file() {
    print_header "Configurando variables de entorno"
    
    if [ -f ".env" ]; then
        print_warning "El archivo .env ya existe."
        read -p "¿Deseas sobrescribirlo? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_message "Manteniendo archivo .env existente."
            return 0
        fi
    fi
    
    print_message "Copiando archivo de ejemplo..."
    cp env.example .env
    
    print_message "Archivo .env creado. Por favor configura tu API key:"
    print_message "  - OPENAI_API_KEY (requerida)"
    print_message ""
    print_message "La API key de OpenAI es necesaria para el funcionamiento del sistema."
}

# Crear directorios necesarios
create_directories() {
    print_header "Creando directorios"
    
    directories=("data/chroma_db" "data/uploads" "logs" "k8s" "monitoring")
    
    for dir in "${directories[@]}"; do
        if [ ! -d "$dir" ]; then
            mkdir -p "$dir"
            print_message "Directorio creado: $dir"
        else
            print_message "Directorio existe: $dir ✓"
        fi
    done
}

# Verificar instalación
verify_installation() {
    print_header "Verificando instalación"
    
    # Activar entorno conda
    print_message "Activando entorno conda..."
    eval "$(conda shell.bash hook)"
    conda activate rag_finanzauto
    
    # Verificar dependencias principales
    print_message "Verificando dependencias principales..."
    
    python -c "import fastapi; print('FastAPI ✓')" 2>/dev/null || print_error "FastAPI no instalado"
    python -c "import chromadb; print('ChromaDB ✓')" 2>/dev/null || print_error "ChromaDB no instalado"
    python -c "import sentence_transformers; print('Sentence-Transformers ✓')" 2>/dev/null || print_error "Sentence-Transformers no instalado"
    
    print_message "Verificación completada."
}

# Mostrar instrucciones finales
show_final_instructions() {
    print_header "¡Instalación completada!"
    
    echo -e "${GREEN}Para ejecutar la aplicación:${NC}"
    echo -e "  1. Activa el entorno conda:"
    echo -e "     ${BLUE}conda activate rag_finanzauto${NC}"
    echo -e ""
    echo -e "  2. Configura tus API keys en el archivo .env"
    echo -e ""
    echo -e "  3. Ejecuta la aplicación:"
    echo -e "     ${BLUE}python app/main.py${NC}"
    echo -e "     o"
    echo -e "     ${BLUE}python -m uvicorn app.main:app --reload${NC}"
    echo -e ""
    echo -e "  4. Accede a la aplicación en: ${BLUE}http://localhost:8000${NC}"
    echo -e "  5. Documentación de la API: ${BLUE}http://localhost:8000/docs${NC}"
    echo -e ""
    
    if command -v docker &> /dev/null; then
        echo -e "${GREEN}Para ejecutar con Docker:${NC}"
        echo -e "  ${BLUE}docker-compose up --build${NC}"
        echo -e ""
    fi
    
    echo -e "${GREEN}Para más información, consulta el README.md${NC}"
}

# Función principal
main() {
    print_header "RAG FinanzAuto - Setup Script"
    
    # Verificar prerrequisitos
    check_conda
    DOCKER_AVAILABLE=$(check_docker && echo "true" || echo "false")
    
    # Configurar entorno
    setup_conda_env
    setup_env_file
    create_directories
    
    # Verificar instalación
    verify_installation
    
    # Mostrar instrucciones finales
    show_final_instructions
    
    print_message "¡Setup completado exitosamente! 🚀"
}

# Ejecutar función principal
main "$@" 