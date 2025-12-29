"""
Nombre del Módulo: middleware.py

Descripción:
Middleware personalizado para PyLucy.
Incluye middleware para deshabilitar caché en modo desarrollo,
evitando problemas con archivos estáticos cacheados durante el desarrollo.

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
