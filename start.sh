#!/bin/bash

# Este script inicia los servicios con Docker Compose, espera a que la aplicación
# principal esté saludable y luego abre la interfaz web en el navegador.

# Argumentos por defecto
PROFILES=()
COMPOSE_CMD="docker compose"

# Parsear argumentos
if [[ " $* " == *" --monitoring "* ]]; then
    echo "🔍 Perfil de monitoreo detectado. Se iniciarán Grafana y Prometheus."
    PROFILES+=("--profile" "monitoring")
fi

# Función para limpiar al salir
cleanup() {
    echo -e "\n🛑 Deteniendo los servicios de Docker..."
    $COMPOSE_CMD ${PROFILES[@]} down
    echo "✅ Servicios detenidos."
    exit 0
}

# Capturar Ctrl+C y llamar a la función de limpieza
trap cleanup SIGINT

# 0. Preparar los assets del frontend
echo "🎨 Preparando assets del frontend..."
SOURCE_LOGO_DIR="logo"
FRONTEND_DIR="frontend"
if [ -d "$SOURCE_LOGO_DIR" ]; then
    cp -rf "$SOURCE_LOGO_DIR" "$FRONTEND_DIR"
    echo "✅ Logo copiado a la carpeta del frontend."
else
    echo "⚠️ Advertencia: No se encontró la carpeta 'logo' en la raíz."
fi

# 1. Iniciar Docker Compose en modo detached (segundo plano)
echo "🚀 Iniciando los servicios de RAG FinanzAuto..."
$COMPOSE_CMD ${PROFILES[@]} up --build -d

if [ $? -ne 0 ]; then
    echo "❌ Error al iniciar Docker Compose. Revisa los logs."
    exit 1
fi

# 2. Esperar a que el contenedor de la aplicación esté saludable
echo -n "⏳ Esperando a que la aplicación esté lista..."

# Timeout después de 2 minutos (120 segundos)
timeout=120
elapsed=0

while [ "$(docker inspect --format='{{.State.Health.Status}}' rag-finanzauto-app 2>/dev/null)" != "healthy" ]; do
    if [ $elapsed -ge $timeout ]; then
        echo -e "\n❌ Timeout: La aplicación no se inició a tiempo."
        echo "   Revisa los logs con el comando: docker compose logs rag-finanzauto-app"
        cleanup
    fi
    
    # Comprobar si el contenedor ha fallado
    status=$(docker inspect --format='{{.State.Status}}' rag-finanzauto-app 2>/dev/null)
    if [ "$status" != "running" ]; then
        echo -e "\n❌ El contenedor 'rag-finanzauto-app' ha fallado. Estado: $status"
        echo "   Revisa los logs con el comando: docker compose logs rag-finanzauto-app"
        cleanup
    fi
    
    echo -n "."
    sleep 5
    elapsed=$((elapsed + 5))
done

# 3. Abrir la interfaz web
echo -e "\n✅ ¡Aplicación lista!"
echo "🌐 Abriendo la interfaz web en http://localhost:8081 ..."
xdg-open http://localhost:8081 &

# Si el monitoreo está activado, mostrar las URLs y abrir Grafana
if [[ " ${PROFILES[*]} " == *"monitoring"* ]]; then
    echo "📊 Accede a Grafana en: http://localhost:3000 (user/pass: admin/admin)"
    echo "📈 Accede a Prometheus en: http://localhost:9090"
    echo "🌐 Abriendo Grafana en tu navegador..."
    # Pequeña pausa para asegurar que el navegador principal ya se ha lanzado
    sleep 2
    xdg-open http://localhost:3000 &
fi

# 4. Mostrar los logs para que el usuario pueda ver la actividad
echo "📄 Mostrando los logs de la API. Presiona Ctrl+C en cualquier momento para detener todo."
$COMPOSE_CMD logs -f rag-app 