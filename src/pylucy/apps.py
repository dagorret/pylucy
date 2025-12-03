"""
Configuración de la aplicación Lucy AMS
"""
from django.apps import AppConfig


class PylucyConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'pylucy'
    verbose_name = 'Lucy AMS'

    def ready(self):
        """
        Método que se ejecuta cuando la aplicación está lista.
        Aquí importamos la configuración del admin.
        """
        from . import admin
