#!/bin/bash
# ==============================================================================
# Script de Deployment para PyLucy - Testing Alfa 1
# ==============================================================================
# Deployment simplificado usando configuración de desarrollo
# Para pruebas internas con acceso a MailHog y PgAdmin
#
# Uso: ./deploy-testing.sh [comando]
# ==============================================================================

set -e

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuración
COMPOSE_FILE="docker-compose.testing.yml"

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

cmd_start() {
    log_info "Iniciando PyLucy Testing (Alfa 1)..."

    # Build si es necesario
    if [ ! "$(docker images -q pylucy-web-testing 2> /dev/null)" ]; then
        log_info "Construyendo imágenes por primera vez..."
        docker compose -f "$COMPOSE_FILE" build
    fi

    # Iniciar servicios
    docker compose -f "$COMPOSE_FILE" up -d

    log_success "Servicios iniciados"

    # Esperar a que la DB esté lista
    log_info "Esperando a que la base de datos esté lista..."
    sleep 10

    # Ejecutar migraciones
    log_info "Ejecutando migraciones..."
    docker compose -f "$COMPOSE_FILE" exec -T web python manage.py migrate

    log_success "PyLucy Testing está corriendo!"
    echo ""
    cmd_info
}

cmd_stop() {
    log_info "Deteniendo PyLucy Testing..."
    docker compose -f "$COMPOSE_FILE" down
    log_success "Servicios detenidos"
}

cmd_restart() {
    cmd_stop
    cmd_start
}

cmd_update() {
    log_info "Actualizando PyLucy Testing..."

    # Pull del código si estamos en git
    if [ -d ".git" ]; then
        log_info "Actualizando código desde Git..."
        git pull
        log_success "Código actualizado"
    fi

    # Rebuild
    log_info "Reconstruyendo imágenes..."
    docker compose -f "$COMPOSE_FILE" build

    # Restart
    cmd_restart
}

cmd_logs() {
    log_info "Mostrando logs (Ctrl+C para salir)..."
    docker compose -f "$COMPOSE_FILE" logs -f
}

cmd_status() {
    log_info "Estado de los servicios:"
    echo ""
    docker compose -f "$COMPOSE_FILE" ps
}

cmd_info() {
    SERVER_IP=$(hostname -I | awk '{print $1}')

    log_success "Información de acceso:"
    echo ""
    echo "  📱 Aplicación Django:"
    echo "     http://$SERVER_IP:8000"
    echo "     http://localhost:8000 (desde el servidor)"
    echo ""
    echo "  👤 Admin Django:"
    echo "     http://$SERVER_IP:8000/admin"
    echo ""
    echo "  📧 MailHog (ver emails):"
    echo "     http://$SERVER_IP:8025"
    echo ""
    echo "  🗄️  PgAdmin (base de datos):"
    echo "     http://$SERVER_IP:5050"
    echo "     Email: admin@unrc.edu.ar"
    echo "     Password: admin"
    echo ""
    log_warning "Puertos expuestos:"
    echo "  - 8000: Django"
    echo "  - 8025: MailHog UI"
    echo "  - 1025: MailHog SMTP"
    echo "  - 5050: PgAdmin"
    echo "  - 5432: PostgreSQL"
    echo "  - 6379: Redis"
    echo ""
}

cmd_superuser() {
    log_info "Creando superusuario de Django..."
    docker compose -f "$COMPOSE_FILE" exec web python manage.py createsuperuser
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

cmd_clean() {
    log_warning "¡CUIDADO! Esto eliminará todos los contenedores y datos"
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

cmd_help() {
    cat << EOF
PyLucy - Deployment Testing Alfa 1

Uso: ./deploy-testing.sh [comando]

Comandos:
  start       - Iniciar servicios (primera vez hace build automático)
  stop        - Detener servicios
  restart     - Reiniciar servicios
  update      - Actualizar código y rebuild
  logs        - Ver logs en tiempo real
  status      - Ver estado de servicios
  info        - Mostrar URLs de acceso
  superuser   - Crear superusuario de Django
  shell       - Abrir shell en contenedor web
  dbshell     - Abrir shell de PostgreSQL
  backup      - Crear backup de base de datos
  clean       - Limpiar todo (¡ELIMINA DATOS!)
  help        - Mostrar esta ayuda

Ejemplos:
  # Primer deployment
  ./deploy-testing.sh start
  ./deploy-testing.sh superuser
  ./deploy-testing.sh info

  # Actualizar después de cambios
  git pull
  ./deploy-testing.sh update

  # Ver logs
  ./deploy-testing.sh logs

EOF
}

# ==============================================================================
# Main
# ==============================================================================

check_requirements

COMMAND=${1:-help}

case "$COMMAND" in
    start)
        cmd_start
        ;;
    stop)
        cmd_stop
        ;;
    restart)
        cmd_restart
        ;;
    update)
        cmd_update
        ;;
    logs)
        cmd_logs
        ;;
    status)
        cmd_status
        ;;
    info)
        cmd_info
        ;;
    superuser)
        cmd_superuser
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
