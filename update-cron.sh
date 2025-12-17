#!/bin/bash

# ============================================
# PyLucy - Configurar Cron/Celery Beat
# ============================================
# Configura tareas periódicas y valores por defecto
# para entornos de testing o producción
#
# Uso:
#   ./update-cron.sh testing
#   ./update-cron.sh prod
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
    CONTAINER_NAME="pylucy-web-testing"
    log_info "Entorno: TESTING"
elif [ "$ENVIRONMENT" == "prod" ]; then
    COMPOSE_FILE="docker-compose.prod.yml"
    CONTAINER_NAME="pylucy-web-prod"
    log_info "Entorno: PRODUCCIÓN"
else
    log_error "Entorno desconocido: $ENVIRONMENT"
    echo "Usa 'testing' o 'prod'"
    exit 1
fi

# Banner
echo ""
echo "============================================"
echo "  PyLucy - Configurar Cron/Celery Beat"
echo "  Entorno: $ENVIRONMENT"
echo "============================================"
echo ""

# 1. Aplicar migraciones (incluye nueva migración de rate_limit_uti)
log_info "Aplicando migraciones pendientes..."
docker compose -f $COMPOSE_FILE exec -T web python manage.py migrate
log_success "Migraciones aplicadas"

# 2. Configurar tareas periódicas en Celery Beat
log_info "Configurando tareas periódicas de Celery Beat..."

# Crear/actualizar tareas periódicas usando Django shell
docker compose -f $COMPOSE_FILE exec -T web python manage.py shell <<EOF
from django_celery_beat.models import PeriodicTask, IntervalSchedule
from alumnos.models import Configuracion
import json

# Cargar configuración
config = Configuracion.load()

# 🔧 TAREA 1: Ingesta de Preinscriptos
# Crear intervalo (cada X segundos según configuración)
interval_pre, created = IntervalSchedule.objects.get_or_create(
    every=config.preinscriptos_frecuencia_segundos,
    period=IntervalSchedule.SECONDS,
)

# Crear/actualizar tarea periódica
task_pre, created = PeriodicTask.objects.update_or_create(
    name='ingesta-preinscriptos',
    defaults={
        'task': 'alumnos.tasks.ingestar_preinscriptos',
        'interval': interval_pre,
        'enabled': bool(config.preinscriptos_dia_inicio),  # Solo habilitado si hay fecha inicio
        'description': 'Ingesta automática de preinscriptos desde SIAL/UTI',
    }
)
print(f"✓ Tarea 'ingesta-preinscriptos': {'creada' if created else 'actualizada'} (intervalo: {config.preinscriptos_frecuencia_segundos}s, habilitada: {bool(config.preinscriptos_dia_inicio)})")

# 🔧 TAREA 2: Ingesta de Aspirantes
interval_asp, created = IntervalSchedule.objects.get_or_create(
    every=config.aspirantes_frecuencia_segundos,
    period=IntervalSchedule.SECONDS,
)

task_asp, created = PeriodicTask.objects.update_or_create(
    name='ingesta-aspirantes',
    defaults={
        'task': 'alumnos.tasks.ingestar_aspirantes',
        'interval': interval_asp,
        'enabled': bool(config.aspirantes_dia_inicio),
        'description': 'Ingesta automática de aspirantes desde SIAL/UTI',
    }
)
print(f"✓ Tarea 'ingesta-aspirantes': {'creada' if created else 'actualizada'} (intervalo: {config.aspirantes_frecuencia_segundos}s, habilitada: {bool(config.aspirantes_dia_inicio)})")

# 🔧 TAREA 3: Ingesta de Ingresantes
interval_ing, created = IntervalSchedule.objects.get_or_create(
    every=config.ingresantes_frecuencia_segundos,
    period=IntervalSchedule.SECONDS,
)

task_ing, created = PeriodicTask.objects.update_or_create(
    name='ingesta-ingresantes',
    defaults={
        'task': 'alumnos.tasks.ingestar_ingresantes',
        'interval': interval_ing,
        'enabled': bool(config.ingresantes_dia_inicio),
        'description': 'Ingesta automática de ingresantes desde SIAL/UTI',
    }
)
print(f"✓ Tarea 'ingesta-ingresantes': {'creada' if created else 'actualizada'} (intervalo: {config.ingresantes_frecuencia_segundos}s, habilitada: {bool(config.ingresantes_dia_inicio)})")

print("\n✅ Tareas periódicas configuradas correctamente")
EOF

log_success "Tareas periódicas configuradas"

# 3. Verificar y cargar valores por defecto de configuración
log_info "Verificando configuración del sistema..."

docker compose -f $COMPOSE_FILE exec -T web python manage.py shell <<EOF
from alumnos.models import Configuracion

config = Configuracion.load()

# 🔧 Asegurar que rate_limit_uti tenga valor por defecto
if not hasattr(config, 'rate_limit_uti') or config.rate_limit_uti is None:
    config.rate_limit_uti = 60
    config.save()
    print("✓ rate_limit_uti configurado: 60/min (default)")
else:
    print(f"✓ rate_limit_uti: {config.rate_limit_uti}/min")

# Mostrar configuración actual
print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("CONFIGURACIÓN ACTUAL:")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print(f"Batch size: {config.batch_size}")
print(f"Rate limit Teams: {config.rate_limit_teams}/min")
print(f"Rate limit Moodle: {config.rate_limit_moodle}/min")
print(f"Rate limit UTI: {config.rate_limit_uti}/min")
print("\nIngesta Preinscriptos:")
print(f"  Inicio: {config.preinscriptos_dia_inicio or 'No configurado'}")
print(f"  Fin: {config.preinscriptos_dia_fin or 'Sin límite'}")
print(f"  Frecuencia: {config.preinscriptos_frecuencia_segundos}s")
print("\nIngesta Aspirantes:")
print(f"  Inicio: {config.aspirantes_dia_inicio or 'No configurado'}")
print(f"  Fin: {config.aspirantes_dia_fin or 'Sin límite'}")
print(f"  Frecuencia: {config.aspirantes_frecuencia_segundos}s")
print("\nIngesta Ingresantes:")
print(f"  Inicio: {config.ingresantes_dia_inicio or 'No configurado'}")
print(f"  Fin: {config.ingresantes_dia_fin or 'Sin límite'}")
print(f"  Frecuencia: {config.ingresantes_frecuencia_segundos}s")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
EOF

log_success "Configuración verificada"

# 4. Reiniciar Celery Beat para que tome los cambios
log_info "Reiniciando Celery Beat..."
docker compose -f $COMPOSE_FILE restart celery-beat
log_success "Celery Beat reiniciado"

# 5. Verificar tareas programadas
log_info "Tareas periódicas registradas:"
echo ""
docker compose -f $COMPOSE_FILE exec -T web python manage.py shell <<EOF
from django_celery_beat.models import PeriodicTask

print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("TAREAS PERIÓDICAS EN CELERY BEAT:")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

tasks = PeriodicTask.objects.all()
for task in tasks:
    status = "✅ Habilitada" if task.enabled else "⏸️  Deshabilitada"
    interval = f"cada {task.interval.every}{task.interval.period}" if task.interval else "N/A"
    print(f"{status} | {task.name}")
    print(f"          Task: {task.task}")
    print(f"          Intervalo: {interval}")
    print()

print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
EOF

echo ""
log_success "¡Configuración de Cron/Celery Beat completada exitosamente!"
echo ""

# Mostrar comandos útiles
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Comandos útiles:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Ver logs de Celery Beat (tareas programadas):"
echo "  docker compose -f $COMPOSE_FILE logs -f celery-beat"
echo ""
echo "Ver logs de Celery Worker (ejecución de tareas):"
echo "  docker compose -f $COMPOSE_FILE logs -f celery"
echo ""
echo "Ver tareas en Django Admin:"
echo "  http://localhost:8000/admin/django_celery_beat/periodictask/"
echo ""
echo "Editar configuración:"
echo "  http://localhost:8000/admin/alumnos/configuracion/"
echo ""
echo "Ver tareas ejecutadas (historial):"
echo "  http://localhost:8000/admin/alumnos/tarea/"
echo ""
echo "Exportar configuración a JSON:"
echo "  docker compose -f $COMPOSE_FILE exec web python manage.py config export"
echo ""
echo "Importar configuración desde JSON:"
echo "  docker compose -f $COMPOSE_FILE exec web python manage.py config import"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
