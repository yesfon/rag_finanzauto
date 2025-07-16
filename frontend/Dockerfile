# Etapa 1: Producción
FROM nginx:alpine

# Limpiar el directorio por defecto de Nginx
RUN rm -rf /usr/share/nginx/html/*

# Copiar solo los assets necesarios (HTML, CSS, JS, logo) al directorio correcto
COPY ./css /usr/share/nginx/html/css
COPY ./js /usr/share/nginx/html/js
COPY ./logo /usr/share/nginx/html/logo
COPY ./index.html /usr/share/nginx/html/

# Exponer el puerto 80
EXPOSE 80

# Comando para iniciar Nginx.
# La configuración será inyectada por Kubernetes a través de un ConfigMap.
CMD ["nginx", "-g", "daemon off;"] 