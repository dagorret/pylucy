"""
Nombre del Módulo: admin.py

Descripción:
Configuración personalizada del Django Admin para Lucy AMS.
Personaliza el sitio de administración con cabeceras, títulos y un índice
personalizado que muestra tareas asíncronas recientes.

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
from django.contrib import admin
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

# Personalización del sitio admin
admin.site.site_header = getattr(settings, 'ADMIN_SITE_HEADER', 'Lucy AMS')
admin.site.site_title = getattr(settings, 'ADMIN_SITE_TITLE', 'Lucy Admin')
admin.site.index_title = getattr(settings, 'ADMIN_INDEX_TITLE', 'Panel de Administración')


# Sobrescribir el index para agregar tareas recientes
def index_with_tasks(self, request, extra_context=None):
    """
    Index del admin personalizado con información de tareas asíncronas.
    """
    from alumnos.models import Tarea

    extra_context = extra_context or {}

    # Tareas recientes (últimas 10)
    tareas_recientes = Tarea.objects.select_related('alumno').order_by('-hora_programada')[:10]

    # Resumen de tareas
    hace_24h = timezone.now() - timedelta(hours=24)
    resumen = {
        'pending': Tarea.objects.filter(estado='pending').count(),
        'running': Tarea.objects.filter(estado='running').count(),
        'completed': Tarea.objects.filter(estado='completed', hora_fin__gte=hace_24h).count(),
        'failed': Tarea.objects.filter(estado='failed', hora_fin__gte=hace_24h).count(),
    }

    extra_context['tareas_recientes'] = tareas_recientes
    extra_context['resumen'] = resumen

    return admin.site.__class__.index(self, request, extra_context)

# Aplicar el método personalizado
admin.site.index = index_with_tasks.__get__(admin.site, admin.site.__class__)
