"""
Configuración de Celery para PyLucy.
"""
import os
from celery import Celery
from celery.schedules import crontab

# Configurar Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pylucy.settings')

app = Celery('pylucy')

# Cargar configuración desde Django settings con prefijo CELERY_
app.config_from_object('django.conf:settings', namespace='CELERY')

# Autodescubrir tareas en todas las apps instaladas
app.autodiscover_tasks()


# =============================================================================
# CELERY BEAT SCHEDULE - Tareas Programadas
# =============================================================================
# NOTA: Las tareas periódicas se configuran desde Django Admin usando
#       django-celery-beat (Admin → Periodic tasks)
#
# Al usar DatabaseScheduler, las tareas se crean/editan dinámicamente
# sin necesidad de reiniciar servicios.
#
# Las tareas se crean automáticamente en la migración de datos:
# - procesar_cola_tareas_pendientes: cada 5 minutos
# - ingestar_preinscriptos: cada 5 minutos
# - ingestar_aspirantes: cada 5 minutos
# - ingestar_ingresantes: cada 5 minutos
# =============================================================================


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
