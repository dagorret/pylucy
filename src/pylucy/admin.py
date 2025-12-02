"""
Configuración personalizada del Django Admin para Lucy AMS
"""
from django.contrib import admin
from django.conf import settings

# Personalización del sitio admin
admin.site.site_header = getattr(settings, 'ADMIN_SITE_HEADER', 'Lucy AMS')
admin.site.site_title = getattr(settings, 'ADMIN_SITE_TITLE', 'Lucy Admin')
admin.site.index_title = getattr(settings, 'ADMIN_INDEX_TITLE', 'Panel de Administración')
