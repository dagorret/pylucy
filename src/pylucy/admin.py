"""
Configuración personalizada del Django Admin para Lucy AMS
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
