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
app.conf.beat_schedule = {
    # Procesador de cola de tareas - CADA 5 MINUTOS
    'procesar-cola-tareas-cada-5min': {
        'task': 'alumnos.tasks.procesar_cola_tareas_pendientes',
        'schedule': crontab(minute='*/5'),  # Cada 5 minutos
        'options': {
            'expires': 240,  # Expira en 4 minutos (antes del siguiente)
        }
    },

    # Ingesta automática de preinscriptos - SEGÚN CONFIGURACIÓN
    'ingestar-preinscriptos': {
        'task': 'alumnos.tasks.ingestar_preinscriptos',
        'schedule': 300.0,  # Cada 5 minutos (la tarea verifica horario internamente)
        'options': {
            'expires': 240,
        }
    },

    # Ingesta automática de aspirantes - SEGÚN CONFIGURACIÓN
    'ingestar-aspirantes': {
        'task': 'alumnos.tasks.ingestar_aspirantes',
        'schedule': 300.0,  # Cada 5 minutos (la tarea verifica horario internamente)
        'options': {
            'expires': 240,
        }
    },

    # Ingesta automática de ingresantes - SEGÚN CONFIGURACIÓN
    'ingestar-ingresantes': {
        'task': 'alumnos.tasks.ingestar_ingresantes',
        'schedule': 300.0,  # Cada 5 minutos (la tarea verifica horario internamente)
        'options': {
            'expires': 240,
        }
    },
}


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
