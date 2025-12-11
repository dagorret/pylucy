"""
Paquete principal de Lucy AMS
"""

# Importar Celery para que se inicie automáticamente
from .celery import app as celery_app

__all__ = ('celery_app',)
