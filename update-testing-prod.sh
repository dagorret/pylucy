#!/bin/bash

# ============================================
# Script de Actualización PyLucy
# ============================================
# Actualiza el código y reinicia servicios en testing o producción
#
# Uso:
#   ./update-testing-prod.sh testing
#   ./update-testing-prod.sh prod
#

set -e  # Salir si hay error

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para mostrar mensajes
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
}

# Verificar parámetro
if [ -z "$1" ]; then
    log_error "Debes especificar el entorno: testing o prod"
    echo ""
    echo "Uso:"
    echo "  $0 testing    # Para entorno de testing"
    echo "  $0 prod       # Para entorno de producción"
    echo ""
    exit 1
fi

ENVIRONMENT=$1

# Configurar según entorno
if [ "$ENVIRONMENT" == "testing" ]; then
    COMPOSE_FILE="docker-compose.testing.yml"
    log_info "Entorno: TESTING"
elif [ "$ENVIRONMENT" == "prod" ]; then
    COMPOSE_FILE="docker-compose.prod.yml"
    log_info "Entorno: PRODUCCIÓN"
else
    log_error "Entorno desconocido: $ENVIRONMENT"
    echo "Usa 'testing' o 'prod'"
    exit 1
fi

# Banner
echo ""
echo "============================================"
echo "  PyLucy - Actualización de Código"
echo "  Entorno: $ENVIRONMENT"
echo "============================================"
echo ""

# 1. Actualizar código desde Git
log_info "Actualizando código desde GitHub..."
git pull origin main
log_success "Código actualizado"

# 2. Verificar si hay migraciones pendientes
log_info "Verificando migraciones..."
PENDING_MIGRATIONS=$(docker compose -f $COMPOSE_FILE exec -T web python manage.py showmigrations --plan | grep "\[ \]" | wc -l || true)

if [ "$PENDING_MIGRATIONS" -gt 0 ]; then
    log_warning "Hay $PENDING_MIGRATIONS migraciones pendientes"
    log_info "Aplicando migraciones..."
    docker compose -f $COMPOSE_FILE exec -T web python manage.py migrate
    log_success "Migraciones aplicadas"
else
    log_success "No hay migraciones pendientes"
fi

# 3. Recolectar archivos estáticos (solo en producción)
if [ "$ENVIRONMENT" == "prod" ]; then
    log_info "Recolectando archivos estáticos..."
    docker compose -f $COMPOSE_FILE exec -T web python manage.py collectstatic --noinput
    log_success "Archivos estáticos recolectados"
fi

# 4. Reiniciar servicios
log_info "Reiniciando servicios (web, celery, celery-beat)..."
docker compose -f $COMPOSE_FILE restart web celery celery-beat
log_success "Servicios reiniciados"

# 5. Verificar estado de servicios
log_info "Verificando estado de servicios..."
sleep 3  # Esperar que los servicios inicien
docker compose -f $COMPOSE_FILE ps

# 6. Verificar logs recientes (últimas 20 líneas)
log_info "Logs recientes de web:"
docker compose -f $COMPOSE_FILE logs --tail=20 web

echo ""
log_success "¡Actualización completada exitosamente!"
echo ""

# Mostrar comandos útiles
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Comandos útiles:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Ver logs en tiempo real:"
echo "  docker compose -f $COMPOSE_FILE logs -f web"
echo ""
echo "Ver estado de servicios:"
echo "  docker compose -f $COMPOSE_FILE ps"
echo ""
echo "Ejecutar shell de Django:"
echo "  docker compose -f $COMPOSE_FILE exec web python manage.py shell"
echo ""
echo "Ver tareas de Celery:"
echo "  docker compose -f $COMPOSE_FILE logs -f celery"
echo ""
echo "Reiniciar solo un servicio:"
echo "  docker compose -f $COMPOSE_FILE restart web"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
