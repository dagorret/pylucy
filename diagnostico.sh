#!/bin/bash
# Script de diagnóstico para problemas de CSS

echo "==================================="
echo "DIAGNÓSTICO PyLucy - Archivos Estáticos"
echo "==================================="
echo ""

echo "1. Verificando estructura de directorios en contenedor..."
docker compose -f docker-compose.testing.yml exec web ls -la /app/ | grep -E "manage.py|pylucy|static"
echo ""

echo "2. Verificando /app/pylucy/static/ existe..."
docker compose -f docker-compose.testing.yml exec web ls -la /app/pylucy/static/
echo ""

echo "3. Verificando archivos CSS..."
docker compose -f docker-compose.testing.yml exec web ls -la /app/pylucy/static/css/
echo ""

echo "4. Verificando configuración Django..."
docker compose -f docker-compose.testing.yml exec web python manage.py shell -c "
from django.conf import settings
import os
print('DEBUG:', settings.DEBUG)
print('STATIC_URL:', settings.STATIC_URL)
print('STATIC_ROOT:', settings.STATIC_ROOT)
print('STATICFILES_DIRS:', settings.STATICFILES_DIRS)
print('')
print('Verificando que el directorio existe:')
for d in settings.STATICFILES_DIRS:
    print(f'  {d}: existe={os.path.exists(d)}')
    if os.path.exists(d):
        print(f'    Archivos: {os.listdir(d)}')
"
echo ""

echo "5. Probando findstatic..."
docker compose -f docker-compose.testing.yml exec web python manage.py findstatic css/tailwind.css
echo ""

echo "6. Probando acceso HTTP al CSS..."
curl -I http://localhost:8000/static/css/tailwind.css 2>&1 | grep -E "^HTTP|^Content"
echo ""

echo "7. Probando acceso HTTP externo..."
IP=$(hostname -I | awk '{print $1}')
curl -I http://$IP:8000/static/css/tailwind.css 2>&1 | grep -E "^HTTP|^Content"
echo ""

echo "==================================="
echo "FIN DEL DIAGNÓSTICO"
echo "==================================="
