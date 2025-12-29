"""
Nombre del Módulo: celery.py

Descripción:
Configuración de Celery para PyLucy.
Define la aplicación Celery, carga configuraciones desde Django settings,
y configura el autodescubrimiento de tareas en todas las apps instaladas.

Autor: Carlos Dagorret
Fecha de Creación: 2025-12-29
Última Modificación: 2025-12-29

Licencia: MIT
Copyright (c) 2025 Carlos Dagorret

Permisos:
Se concede permiso, de forma gratuita, a cualquier persona que obtenga una copia
de este software y la documentación asociada (el "Software"), para tratar
en el Software sin restricciones, incluyendo, sin limitación, los derechos
de usar, copiar, modificar, fusionar, publicar, distribuir, sublicenciar
y/o vender copias del Software, y para permitir a las personas a las que
se les proporciona el Software hacerlo, sujeto a las siguientes condiciones:

El aviso de copyright anterior y este aviso de permiso se incluirán en todas
las copias o partes sustanciales del Software.

EL SOFTWARE SE PROPORCIONA "TAL CUAL", SIN GARANTÍA DE NINGÚN TIPO, EXPRESA O
IMPLÍCITA, INCLUYENDO PERO NO LIMITADO A LAS GARANTÍAS DE COMERCIABILIDAD,
IDONEIDAD PARA UN PROPÓSITO PARTICULAR Y NO INFRACCIÓN. EN NINGÚN CASO LOS
AUTORES O TITULARES DE LOS DERECHOS DE AUTOR SERÁN RESPONSABLES DE CUALQUIER
RECLAMO, DAÑO U OTRA RESPONSABILIDAD, YA SEA EN UNA ACCIÓN DE CONTRATO,
AGRAVIO O DE OTRO MODO, QUE SURJA DE, FUERA DE O EN CONEXIÓN CON EL SOFTWARE
O EL USO U OTROS TRATOS EN EL SOFTWARE.
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
