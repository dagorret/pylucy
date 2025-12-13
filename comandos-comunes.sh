#!/bin/bash

# ============================================
# Comandos Comunes PyLucy
# ============================================
# Colección de comandos útiles para operación diaria
#
# Uso:
#   ./comandos-comunes.sh [comando] [entorno]
#
# Ejemplos:
#   ./comandos-comunes.sh logs testing
#   ./comandos-comunes.sh shell prod
#   ./comandos-comunes.sh status testing
#

set -e

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Función para mostrar ayuda
show_help() {
    echo ""
    echo "============================================"
    echo "  PyLucy - Comandos Comunes"
    echo "============================================"
    echo ""
    echo "Uso: $0 [comando] [entorno]"
    echo ""
    echo "Entornos disponibles:"
    echo "  testing    - Entorno de testing"
    echo "  prod       - Entorno de producción"
    echo ""
    echo "Comandos disponibles:"
    echo ""
    echo "  ${GREEN}status${NC}          - Ver estado de todos los servicios"
    echo "  ${GREEN}logs${NC}            - Ver logs en tiempo real (web)"
    echo "  ${GREEN}logs-all${NC}        - Ver logs de todos los servicios"
    echo "  ${GREEN}logs-celery${NC}     - Ver logs de Celery worker"
    echo "  ${GREEN}logs-beat${NC}       - Ver logs de Celery beat"
    echo "  ${GREEN}shell${NC}           - Abrir shell de Django"
    echo "  ${GREEN}dbshell${NC}         - Abrir shell de PostgreSQL"
    echo "  ${GREEN}migrate${NC}         - Aplicar migraciones pendientes"
    echo "  ${GREEN}makemigrations${NC}  - Crear nuevas migraciones"
    echo "  ${GREEN}collectstatic${NC}   - Recolectar archivos estáticos"
    echo "  ${GREEN}restart${NC}         - Reiniciar todos los servicios"
    echo "  ${GREEN}restart-web${NC}     - Reiniciar solo web"
    echo "  ${GREEN}restart-celery${NC}  - Reiniciar solo celery"
    echo "  ${GREEN}backup-db${NC}       - Hacer backup de base de datos"
    echo "  ${GREEN}import-config${NC}   - Importar configuración desde JSON"
    echo "  ${GREEN}export-config${NC}   - Exportar configuración a JSON"
    echo "  ${GREEN}verify-config${NC}   - Verificar configuración actual"
    echo ""
    echo "Ejemplos:"
    echo "  $0 logs testing"
    echo "  $0 shell prod"
    echo "  $0 status testing"
    echo "  $0 backup-db prod"
    echo ""
}

# Verificar parámetros
if [ -z "$1" ] || [ -z "$2" ]; then
    show_help
    exit 1
fi

COMMAND=$1
ENVIRONMENT=$2

# Configurar compose file
if [ "$ENVIRONMENT" == "testing" ]; then
    COMPOSE_FILE="docker-compose.testing.yml"
    CONTAINER_PREFIX="pylucy-web-testing"
elif [ "$ENVIRONMENT" == "prod" ]; then
    COMPOSE_FILE="docker-compose.prod.yml"
    CONTAINER_PREFIX="pylucy-web-prod"
else
    echo -e "${RED}[✗]${NC} Entorno desconocido: $ENVIRONMENT"
    echo "Usa 'testing' o 'prod'"
    exit 1
fi

echo -e "${BLUE}[INFO]${NC} Ejecutando: ${GREEN}$COMMAND${NC} en entorno: ${CYAN}$ENVIRONMENT${NC}"
echo ""

# Ejecutar comando
case $COMMAND in
    status)
        docker compose -f $COMPOSE_FILE ps
        ;;

    logs)
        docker compose -f $COMPOSE_FILE logs -f --tail=100 web
        ;;

    logs-all)
        docker compose -f $COMPOSE_FILE logs -f --tail=50
        ;;

    logs-celery)
        docker compose -f $COMPOSE_FILE logs -f --tail=100 celery
        ;;

    logs-beat)
        docker compose -f $COMPOSE_FILE logs -f --tail=100 celery-beat
        ;;

    shell)
        docker compose -f $COMPOSE_FILE exec web python manage.py shell
        ;;

    dbshell)
        docker compose -f $COMPOSE_FILE exec db psql -U pylucy -d pylucy
        ;;

    migrate)
        docker compose -f $COMPOSE_FILE exec web python manage.py migrate
        ;;

    makemigrations)
        docker compose -f $COMPOSE_FILE exec web python manage.py makemigrations
        ;;

    collectstatic)
        docker compose -f $COMPOSE_FILE exec web python manage.py collectstatic --noinput
        ;;

    restart)
        docker compose -f $COMPOSE_FILE restart web celery celery-beat
        echo -e "${GREEN}[✓]${NC} Servicios reiniciados"
        ;;

    restart-web)
        docker compose -f $COMPOSE_FILE restart web
        echo -e "${GREEN}[✓]${NC} Web reiniciado"
        ;;

    restart-celery)
        docker compose -f $COMPOSE_FILE restart celery celery-beat
        echo -e "${GREEN}[✓]${NC} Celery reiniciado"
        ;;

    backup-db)
        TIMESTAMP=$(date +%Y%m%d_%H%M%S)
        BACKUP_FILE="backup_${ENVIRONMENT}_${TIMESTAMP}.sql"
        echo -e "${BLUE}[INFO]${NC} Creando backup: $BACKUP_FILE"
        docker compose -f $COMPOSE_FILE exec -T db pg_dump -U pylucy pylucy > $BACKUP_FILE
        echo -e "${GREEN}[✓]${NC} Backup creado: $BACKUP_FILE"
        ;;

    import-config)
        if [ ! -f "configuracion_real.json" ]; then
            echo -e "${RED}[✗]${NC} Archivo configuracion_real.json no encontrado"
            exit 1
        fi
        docker cp configuracion_real.json ${CONTAINER_PREFIX}:/app/configuracion_real.json
        docker compose -f $COMPOSE_FILE exec web python manage.py config import --file /app/configuracion_real.json
        echo -e "${GREEN}[✓]${NC} Configuración importada"
        ;;

    export-config)
        TIMESTAMP=$(date +%Y%m%d_%H%M%S)
        CONFIG_FILE="config_export_${ENVIRONMENT}_${TIMESTAMP}.json"
        docker compose -f $COMPOSE_FILE exec web python manage.py config export --file /app/config_export.json
        docker cp ${CONTAINER_PREFIX}:/app/config_export.json ./$CONFIG_FILE
        echo -e "${GREEN}[✓]${NC} Configuración exportada: $CONFIG_FILE"
        ;;

    verify-config)
        docker compose -f $COMPOSE_FILE exec web python manage.py shell -c "from alumnos.models import Configuracion; c = Configuracion.load(); print('Teams Tenant:', c.teams_tenant_id); print('SIAL URL:', c.sial_base_url); print('Moodle:', c.moodle_base_url); print('Plantillas cargadas:', len(c.email_plantilla_bienvenida)>0)"
        ;;

    *)
        echo -e "${RED}[✗]${NC} Comando desconocido: $COMMAND"
        show_help
        exit 1
        ;;
esac
