#!/bin/bash
# debug_frontend_pod.sh

# Este script se debe ejecutar con kubectl para diagnosticar el estado
# de los archivos y la configuración dentro del pod del frontend.

echo "--- 1. Información del Pod ---"
echo "Hostname: $(hostname)"
echo "Usuario actual: $(whoami)"
echo ""

echo "--- 2. Contenido del Directorio Web Raíz (/usr/share/nginx/html) ---"
ls -lR /usr/share/nginx/html/
echo ""

echo "--- 3. Contenido del index.html ---"
echo "Contenido de /usr/share/nginx/html/index.html:"
cat /usr/share/nginx/html/index.html
echo ""
echo "--- Fin del index.html ---"
echo ""

echo "--- 4. Configuración de Nginx en Uso ---"
echo "Contenido de /etc/nginx/conf.d/default.conf:"
cat /etc/nginx/conf.d/default.conf
echo ""
echo "--- Fin de la configuración de Nginx ---"
echo ""

echo "--- 5. Proceso de Nginx Corriendo ---"
ps aux | grep nginx
echo ""

echo "--- Depuración finalizada ---" 