"""
Middleware personalizado para PyLucy
"""
import os
from django.conf import settings


class NoCacheMiddleware:
    """
    Middleware para deshabilitar caché en desarrollo local.
    Agrega headers para que el navegador no cachee archivos estáticos.

    IMPORTANTE: Solo se activa en modo 'development' (no en testing ni producción).
    Controlado por la variable ENVIRONMENT_MODE en .env
    """
    def __init__(self, get_response):
        self.get_response = get_response
        # Leer modo del entorno
        self.environment_mode = os.getenv('ENVIRONMENT_MODE', 'production')

    def __call__(self, request):
        response = self.get_response(request)

        # Solo aplicar en modo development (no en testing ni production)
        if self.environment_mode == 'development':
            # Solo aplicar en rutas del admin y archivos estáticos
            if request.path.startswith('/admin/') or request.path.startswith('/static/'):
                response['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
                response['Pragma'] = 'no-cache'
                response['Expires'] = '0'

        return response
