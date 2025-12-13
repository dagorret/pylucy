"""
URL configuration for moodlestats project.
"""
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from moodledata.admin import admin_site

urlpatterns = [
    path('admin/', admin_site.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
