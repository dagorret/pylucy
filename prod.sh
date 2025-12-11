#!/usr/bin/env bash
# Script para levantar entorno de PRODUCCIÓN
set -e

echo "⚠️  INICIANDO MODO PRODUCCIÓN"
echo "================================"
echo ""

# Verificar que existe .env.prod
if [ ! -f .env.prod ]; then
    echo "❌ ERROR: Archivo .env.prod no encontrado"
    echo ""
    echo "Copiar .env.prod.example y configurar:"
    echo "  cp .env.prod.example .env.prod"
    echo "  nano .env.prod"
    echo ""
    echo "Variables críticas a configurar:"
    echo "  - DB_PASSWORD (contraseña de PostgreSQL)"
    echo "  - SECRET_KEY (clave secreta de Django)"
    echo "  - ALLOWED_HOSTS (dominio del servidor)"
    echo "  - EMAIL_PASSWORD (contraseña SMTP)"
    echo "  - TEAMS_TENANT, TEAMS_CLIENT_ID, TEAMS_CLIENT_SECRET"
    echo "  - MOODLE_BASE_URL, MOODLE_WSTOKEN"
    echo ""
    exit 1
fi

echo "✓ Archivo .env.prod encontrado"
echo ""

# Verificar que Docker está corriendo
if ! docker info > /dev/null 2>&1; then
    echo "❌ ERROR: Docker no está corriendo"
    echo "Iniciar Docker primero"
    exit 1
fi

echo "✓ Docker está corriendo"
echo ""

# Detener servicios previos si existen
echo "Deteniendo servicios previos (si existen)..."
docker compose -f docker-compose.prod.yml down 2>/dev/null || true
echo ""

# Build y levantar servicios
echo "Construyendo imágenes..."
docker compose -f docker-compose.prod.yml --env-file .env.prod build

echo ""
echo "Levantando servicios..."
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d

echo ""
echo "Esperando a que los servicios estén listos..."
sleep 10

# Verificar servicios
echo ""
echo "Estado de los servicios:"
docker compose -f docker-compose.prod.yml ps

echo ""
echo "✓ Servicios levantados en modo PRODUCCIÓN"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  ACCESOS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Aplicación: http://localhost"
echo "  Admin:      http://localhost/admin"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  COMANDOS ÚTILES"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  Ver logs en tiempo real:"
echo "    docker compose -f docker-compose.prod.yml logs -f"
echo ""
echo "  Ver logs de un servicio específico:"
echo "    docker compose -f docker-compose.prod.yml logs -f web"
echo "    docker compose -f docker-compose.prod.yml logs -f celery"
echo ""
echo "  Ejecutar comando Django:"
echo "    docker compose -f docker-compose.prod.yml exec web python manage.py <comando>"
echo ""
echo "  Crear superusuario:"
echo "    docker compose -f docker-compose.prod.yml exec web python manage.py createsuperuser"
echo ""
echo "  Acceder a shell de Django:"
echo "    docker compose -f docker-compose.prod.yml exec web python manage.py shell"
echo ""
echo "  Reiniciar servicios:"
echo "    docker compose -f docker-compose.prod.yml restart"
echo ""
echo "  Detener todos los servicios:"
echo "    docker compose -f docker-compose.prod.yml down"
echo ""
echo "  Ver estado de servicios:"
echo "    docker compose -f docker-compose.prod.yml ps"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
