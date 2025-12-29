"""
Nombre del Módulo: settings.py

Descripción:
Configuración principal del proyecto Django PyLucy (Lucy AMS).
Define configuraciones de base de datos, aplicaciones instaladas, middleware,
configuración de email, Celery, integración con SIAL/UTI, Moodle y Microsoft Teams.

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
from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent



# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
# Nunca hardcodear SECRET_KEY en el código fuente
SECRET_KEY = os.getenv(
    'DJANGO_SECRET_KEY',
    'django-insecure-CHANGE_THIS_IN_PRODUCTION_USE_ENVIRONMENT_VARIABLE'
)

# SECURITY WARNING: don't run with debug turned on in production!
# DEBUG = True

# ALLOWED_HOSTS = []

DEBUG = os.getenv("DJANGO_DEBUG", "True").lower() == "true"

ALLOWED_HOSTS = os.getenv("DJANGO_ALLOWED_HOSTS", "").split() or ["localhost", "127.0.0.1"]



# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_select2',
    'django_celery_beat',  # Tareas programadas con BD
    'alumnos',
    'cursos',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'pylucy.middleware.NoCacheMiddleware',  # Deshabilitar caché en desarrollo
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'pylucy.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'pylucy' / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'pylucy.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

# DATABASES = {
#    'default': {
#        'ENGINE': 'django.db.backends.sqlite3',
#        'NAME': BASE_DIR / 'db.sqlite3',
#    }
#}

DATABASES = {
    "default": {
        "ENGINE": os.getenv("DB_ENGINE", "django.db.backends.postgresql"),
        "NAME": os.getenv("DB_NAME", "pylucy"),
        "USER": os.getenv("DB_USER", "pylucy"),
        "PASSWORD": os.getenv("DB_PASSWORD", "pylucy"),
        "HOST": os.getenv("DB_HOST", "localhost"),  # en Docker será "db"
        "PORT": os.getenv("DB_PORT", "5432"),
    }
}

# Configuración de la API SIAL/UTI (mock o producción)
# Las credenciales se cargan desde credenciales/uti_credentials.json
# o desde variables de entorno como fallback
try:
    from pylucy.credentials_loader import get_uti_credentials
    _uti_creds = get_uti_credentials()
    SIAL_BASE_URL = _uti_creds['base_url'].rstrip("/")
    SIAL_BASIC_USER = _uti_creds['username']
    SIAL_BASIC_PASS = _uti_creds['password']
except Exception as e:
    print(f"⚠️  Error cargando credenciales UTI: {e}")
    SIAL_BASE_URL = os.getenv("SIAL_BASE_URL", "http://localhost:8088").rstrip("/")
    SIAL_BASIC_USER = os.getenv("SIAL_BASIC_USER", "usuario")
    SIAL_BASIC_PASS = os.getenv("SIAL_BASIC_PASS", "contrasena")


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'es-ar'

TIME_ZONE = 'America/Argentina/Cordoba'

USE_I18N = True

USE_TZ = True

# Regional formatting for Argentina
USE_L10N = True
USE_THOUSAND_SEPARATOR = True
DECIMAL_SEPARATOR = ","
THOUSAND_SEPARATOR = "."


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = 'static/'
STATICFILES_DIRS = [
    BASE_DIR / 'static',  # /app/static/ cuando se monta ./src:/app
    BASE_DIR / 'pylucy' / 'static',  # /app/pylucy/static/ - archivos CSS personalizados del admin
]
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Admin site customization
ADMIN_SITE_HEADER = "Lucy AMS"
ADMIN_SITE_TITLE = "Lucy Admin"
ADMIN_INDEX_TITLE = "Panel de Administración"

# Email configuration
# =============================================================================
# CONFIGURACIÓN DE EMAIL (Office 365 / SMTP)
# =============================================================================
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"

# Office 365 SMTP: smtp.office365.com:587 (TLS)
# MailHog (dev): mailhog:1025 (sin auth)
EMAIL_HOST = os.getenv("EMAIL_HOST", "mailhog")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "1025"))
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "False").lower() == "true"
EMAIL_USE_SSL = os.getenv("EMAIL_USE_SSL", "False").lower() == "true"
DEFAULT_FROM_EMAIL = os.getenv("EMAIL_FROM", "no-reply@v.eco.unrc.edu.ar")
EMAIL_FROM = DEFAULT_FROM_EMAIL  # Alias para consistencia

ALLOWED_HOSTS = ['*']

# =============================================================================
# CONFIGURACIÓN TESTING vs PRODUCCIÓN (#ETME)
# =============================================================================

# Modo de ejecución (testing o production)
ENVIRONMENT_MODE = os.getenv("ENVIRONMENT_MODE", "testing").lower()

# Prefijo para cuentas de testing
# testing: test-a12345678@eco.unrc.edu.ar
# production: a12345678@eco.unrc.edu.ar
ACCOUNT_PREFIX = "test-a" if ENVIRONMENT_MODE == "testing" else "a"

# Moodle - Las credenciales se cargan desde credenciales/moodle_credentials.json
try:
    from pylucy.credentials_loader import get_moodle_credentials
    _moodle_creds = get_moodle_credentials()
    MOODLE_BASE_URL = _moodle_creds['base_url']
    MOODLE_WSTOKEN = _moodle_creds['wstoken']
except Exception as e:
    print(f"⚠️  Error cargando credenciales Moodle: {e}")
    MOODLE_BASE_URL = os.getenv(
        "MOODLE_BASE_URL",
        "https://sandbox.moodledemo.net" if ENVIRONMENT_MODE == "testing" else "https://moodle.eco.unrc.edu.ar"
    )
    MOODLE_WSTOKEN = os.getenv("MOODLE_WSTOKEN", "")

# Microsoft Teams / Graph API - Las credenciales se cargan desde credenciales/teams_credentials.json
try:
    from pylucy.credentials_loader import get_teams_credentials
    _teams_creds = get_teams_credentials()
    TEAMS_TENANT = _teams_creds['tenant_id']
    TEAMS_DOMAIN = _teams_creds['domain']
    TEAMS_CLIENT_ID = _teams_creds['client_id']
    TEAMS_CLIENT_SECRET = _teams_creds['client_secret']
except Exception as e:
    print(f"⚠️  Error cargando credenciales Teams: {e}")
    TEAMS_TENANT = os.getenv("TEAMS_TENANT", "")
    TEAMS_DOMAIN = os.getenv("TEAMS_DOMAIN", "eco.unrc.edu.ar")
    TEAMS_CLIENT_ID = os.getenv("TEAMS_CLIENT_ID", "")
    TEAMS_CLIENT_SECRET = os.getenv("TEAMS_CLIENT_SECRET", "")

# =============================================================================
# CELERY CONFIGURATION
# =============================================================================
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'

# =============================================================================
# SISTEMA DE COLAS - Feature Flag
# =============================================================================
# Controla si las acciones del admin usan el nuevo sistema de colas con
# procesamiento cada 5 minutos (True) o ejecutan inmediatamente con .delay() (False)
#
# True:  Las acciones crean registros Tarea(estado=PENDING) y el procesador
#        los ejecuta cada 5 min respetando batch_size y rate_limits
# False: Las acciones llaman .delay() inmediatamente (comportamiento anterior)
#
# Para activar en producción/testing: agregar USE_QUEUE_SYSTEM=true en .env
USE_QUEUE_SYSTEM = os.getenv("USE_QUEUE_SYSTEM", "False").lower() == "true"
