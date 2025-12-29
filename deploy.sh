#!/bin/bash
# ==============================================================================
# Script de Deployment para PyLucy - Servidor de Testing
# ==============================================================================
# Este script facilita el deployment en el servidor de testing
# Uso: ./deploy.sh [comando]
#
# Comandos disponibles:
#   setup    - Primera instalación (crear .env.prod)
#   update   - Actualizar código y rebuild
#   start    - Iniciar los servicios
#   stop     - Detener los servicios
#   restart  - Reiniciar los servicios
#   logs     - Ver logs de los servicios
#   status   - Ver estado de los servicios
#   clean    - Limpiar contenedores y volúmenes (¡CUIDADO!)
# ==============================================================================

set -e  # Salir si hay algún error

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuración
COMPOSE_FILE="docker-compose.prod.yml"
ENV_FILE=".env.prod"
ENV_EXAMPLE=".env.prod.example"

# ==============================================================================
# Funciones de utilidad
# ==============================================================================

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_requirements() {
    log_info "Verificando requisitos..."

    if ! command -v docker &> /dev/null; then
        log_error "Docker no está instalado"
        exit 1
    fi

    if ! command -v docker compose &> /dev/null; then
        log_error "Docker Compose no está instalado"
        exit 1
    fi

    log_success "Requisitos verificados"
}

check_env_file() {
    if [ ! -f "$ENV_FILE" ]; then
        log_error "No existe $ENV_FILE"
        log_warning "Ejecuta primero: ./deploy.sh setup"
        exit 1
    fi
}

# ==============================================================================
# Comandos
# ==============================================================================

cmd_setup() {
    log_info "Configuración inicial de PyLucy..."

    # Verificar si ya existe .env.prod
    if [ -f "$ENV_FILE" ]; then
        log_warning "$ENV_FILE ya existe"
        read -p "¿Deseas sobrescribirlo? (s/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Ss]$ ]]; then
            log_info "Operación cancelada"
            exit 0
        fi
    fi

    # Copiar archivo de ejemplo
    if [ ! -f "$ENV_EXAMPLE" ]; then
        log_error "No existe $ENV_EXAMPLE"
        exit 1
    fi

    cp "$ENV_EXAMPLE" "$ENV_FILE"
    log_success "Archivo $ENV_FILE creado"

    # Generar SECRET_KEY
    log_info "Generando SECRET_KEY..."
    SECRET_KEY=$(python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())" 2>/dev/null || echo "CAMBIAR_ESTO_POR_SECRET_KEY_SEGURA")

    # Reemplazar en .env.prod
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' "s|SECRET_KEY=CAMBIAR_POR_CLAVE_SECRETA_GENERADA|SECRET_KEY=$SECRET_KEY|g" "$ENV_FILE"
    else
        # Linux
        sed -i "s|SECRET_KEY=CAMBIAR_POR_CLAVE_SECRETA_GENERADA|SECRET_KEY=$SECRET_KEY|g" "$ENV_FILE"
    fi

    log_success "SECRET_KEY generada"

    echo ""
    log_warning "IMPORTANTE: Edita $ENV_FILE y configura:"
    echo "  1. DB_PASSWORD (contraseña de PostgreSQL)"
    echo "  2. ALLOWED_HOSTS (dominio del servidor)"
    echo "  3. SIAL_BASE_URL, SIAL_BASIC_USER, SIAL_BASIC_PASS"
    echo "  4. MOODLE_BASE_URL, MOODLE_WSTOKEN"
    echo "  5. EMAIL_HOST, EMAIL_HOST_USER, EMAIL_HOST_PASSWORD"
    echo "  6. TEAMS_TENANT, TEAMS_CLIENT_ID, TEAMS_CLIENT_SECRET"
    echo ""
    log_info "Una vez editado, ejecuta: ./deploy.sh start"
}

cmd_update() {
    log_info "Actualizando PyLucy..."
    check_env_file

    # Pull del código (si estamos en el servidor)
    if [ -d ".git" ]; then
        log_info "Actualizando código desde Git..."
        git pull
        log_success "Código actualizado"
    fi

    # Rebuild de las imágenes
    log_info "Construyendo imágenes Docker..."
    docker compose -f "$COMPOSE_FILE" build --no-cache
    log_success "Imágenes construidas"

    # Restart de los servicios
    log_info "Reiniciando servicios..."
    docker compose -f "$COMPOSE_FILE" down
    docker compose -f "$COMPOSE_FILE" up -d

    # Esperar a que la DB esté lista
    log_info "Esperando a que la base de datos esté lista..."
    sleep 10

    # Verificar y resolver conflictos de migraciones
    log_info "Verificando migraciones..."

    # Detectar si hay conflictos de migraciones
    CONFLICTS=$(docker compose -f "$COMPOSE_FILE" exec -T web python manage.py showmigrations 2>&1 | grep -c "CONFLICT" || true)

    if [ "$CONFLICTS" -gt 0 ]; then
        log_warning "Detectados conflictos de migraciones. Mergeando automáticamente..."
        docker compose -f "$COMPOSE_FILE" exec -T web python manage.py makemigrations --merge --noinput || {
            log_error "Error al mergear migraciones. Por favor revisa manualmente."
            exit 1
        }
        log_success "Conflictos de migraciones resueltos"
    fi

    # Ejecutar migraciones
    log_info "Aplicando migraciones..."
    if ! docker compose -f "$COMPOSE_FILE" exec -T web python manage.py migrate; then
        log_error "Error al aplicar migraciones"
        log_info "Revisa los logs con: ./deploy.sh logs"
        exit 1
    fi

    log_success "Migraciones aplicadas correctamente"

    # Recolectar static files
    log_info "Recolectando archivos estáticos..."
    docker compose -f "$COMPOSE_FILE" exec -T web python manage.py collectstatic --noinput

    log_success "Actualización completada"
    cmd_status
}

cmd_start() {
    log_info "Iniciando PyLucy..."
    check_env_file

    # Iniciar servicios
    docker compose -f "$COMPOSE_FILE" up -d

    log_success "Servicios iniciados"
    sleep 5
    cmd_status
}

cmd_stop() {
    log_info "Deteniendo PyLucy..."
    docker compose -f "$COMPOSE_FILE" down
    log_success "Servicios detenidos"
}

cmd_restart() {
    log_info "Reiniciando PyLucy..."
    cmd_stop
    cmd_start
}

cmd_logs() {
    log_info "Mostrando logs (Ctrl+C para salir)..."
    docker compose -f "$COMPOSE_FILE" logs -f
}

cmd_status() {
    log_info "Estado de los servicios:"
    echo ""
    docker compose -f "$COMPOSE_FILE" ps
    echo ""

    # Verificar healthchecks
    log_info "Estado de salud de los contenedores:"
    docker compose -f "$COMPOSE_FILE" ps --format json | python3 -c "
import json
import sys
try:
    data = json.load(sys.stdin)
    if isinstance(data, dict):
        data = [data]
    for container in data:
        name = container.get('Name', 'N/A')
        status = container.get('Status', 'N/A')
        health = container.get('Health', 'N/A')
        print(f'  {name}: {status} - Health: {health}')
except:
    pass
" || docker compose -f "$COMPOSE_FILE" ps
}

cmd_clean() {
    log_warning "¡CUIDADO! Esto eliminará todos los contenedores y volúmenes"
    log_warning "Se perderán TODOS LOS DATOS de la base de datos y Redis"
    read -p "¿Estás seguro? Escribe 'SI' para confirmar: " -r
    echo
    if [[ $REPLY != "SI" ]]; then
        log_info "Operación cancelada"
        exit 0
    fi

    log_info "Eliminando contenedores y volúmenes..."
    docker compose -f "$COMPOSE_FILE" down -v
    log_success "Limpieza completada"
}

cmd_shell() {
    log_info "Abriendo shell en el contenedor web..."
    docker compose -f "$COMPOSE_FILE" exec web /bin/bash
}

cmd_dbshell() {
    log_info "Abriendo shell de PostgreSQL..."
    docker compose -f "$COMPOSE_FILE" exec db psql -U pylucy -d pylucy
}

cmd_backup() {
    log_info "Creando backup de la base de datos..."
    BACKUP_FILE="backup_$(date +%Y%m%d_%H%M%S).sql"
    docker compose -f "$COMPOSE_FILE" exec -T db pg_dump -U pylucy pylucy > "$BACKUP_FILE"
    log_success "Backup creado: $BACKUP_FILE"
}

cmd_help() {
    cat << EOF
PyLucy - Script de Deployment para Testing

Uso: ./deploy.sh [comando]

Comandos disponibles:
  setup      - Primera instalación (crear .env.prod y configurar)
  update     - Actualizar código y rebuild de imágenes
  start      - Iniciar los servicios
  stop       - Detener los servicios
  restart    - Reiniciar los servicios
  logs       - Ver logs en tiempo real (Ctrl+C para salir)
  status     - Ver estado de los servicios
  shell      - Abrir shell en el contenedor web
  dbshell    - Abrir shell de PostgreSQL
  backup     - Crear backup de la base de datos
  clean      - Limpiar contenedores y volúmenes (¡CUIDADO!)
  help       - Mostrar esta ayuda

Ejemplos:
  # Primera instalación
  ./deploy.sh setup
  # Editar .env.prod con tus valores
  ./deploy.sh start

  # Actualizar después de cambios en Git
  ./deploy.sh update

  # Ver logs
  ./deploy.sh logs

  # Crear backup antes de actualizar
  ./deploy.sh backup
  ./deploy.sh update

EOF
}

# ==============================================================================
# Main
# ==============================================================================

check_requirements

COMMAND=${1:-help}

case "$COMMAND" in
    setup)
        cmd_setup
        ;;
    update)
        cmd_update
        ;;
    start)
        cmd_start
        ;;
    stop)
        cmd_stop
        ;;
    restart)
        cmd_restart
        ;;
    logs)
        cmd_logs
        ;;
    status)
        cmd_status
        ;;
    shell)
        cmd_shell
        ;;
    dbshell)
        cmd_dbshell
        ;;
    backup)
        cmd_backup
        ;;
    clean)
        cmd_clean
        ;;
    help|--help|-h)
        cmd_help
        ;;
    *)
        log_error "Comando desconocido: $COMMAND"
        cmd_help
        exit 1
        ;;
esac
