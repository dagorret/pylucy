"""
Utilidades para obtener configuración del sistema.
Lee primero de la base de datos (modelo Configuracion),
y si no existe, usa variables de entorno por defecto.
"""

from django.conf import settings
from typing import Optional


def get_moodle_base_url() -> str:
    """
    Obtiene la URL base de Moodle.

    Orden de prioridad:
    1. Configuración en base de datos (si existe y no está vacía)
    2. Variable de entorno MOODLE_BASE_URL
    3. Default: sandbox de Moodle

    Returns:
        str: URL base de Moodle
    """
    try:
        from alumnos.models import Configuracion
        config = Configuracion.objects.first()
        if config and config.moodle_base_url:
            return config.moodle_base_url
    except Exception:
        # Si hay error al leer BD (ej: migraciones no ejecutadas), usar env
        pass

    return settings.MOODLE_BASE_URL


def get_moodle_wstoken() -> str:
    """
    Obtiene el token de Moodle WebServices.

    Orden de prioridad:
    1. Configuración en base de datos (si existe y no está vacía)
    2. Variable de entorno MOODLE_WSTOKEN
    3. Default: string vacío

    Returns:
        str: Token de Moodle WS
    """
    try:
        from alumnos.models import Configuracion
        config = Configuracion.objects.first()
        if config and config.moodle_wstoken:
            return config.moodle_wstoken
    except Exception:
        # Si hay error al leer BD, usar env
        pass

    return settings.MOODLE_WSTOKEN


def get_sial_base_url() -> str:
    """
    Obtiene la URL base de SIAL/UTI API.

    Orden de prioridad:
    1. Configuración en base de datos (si existe y no está vacía)
    2. Variable de entorno SIAL_BASE_URL
    3. Default: http://localhost:8088

    Returns:
        str: URL base de SIAL/UTI
    """
    try:
        from alumnos.models import Configuracion
        config = Configuracion.objects.first()
        if config and config.sial_base_url:
            return config.sial_base_url
    except Exception:
        # Si hay error al leer BD, usar env
        pass

    return settings.SIAL_BASE_URL


def get_rate_limit_moodle() -> int:
    """
    Obtiene el rate limit de Moodle (requests por minuto).

    Returns:
        int: Máximo de requests por minuto
    """
    try:
        from alumnos.models import Configuracion
        config = Configuracion.objects.first()
        if config:
            return config.rate_limit_moodle
    except Exception:
        pass

    return 30  # Default


def get_rate_limit_teams() -> int:
    """
    Obtiene el rate limit de Teams (requests por minuto).

    Returns:
        int: Máximo de requests por minuto
    """
    try:
        from alumnos.models import Configuracion
        config = Configuracion.objects.first()
        if config:
            return config.rate_limit_teams
    except Exception:
        pass

    return 10  # Default


def get_batch_size() -> int:
    """
    Obtiene el tamaño de lote para procesamiento.

    Returns:
        int: Cantidad de elementos a procesar por lote
    """
    try:
        from alumnos.models import Configuracion
        config = Configuracion.objects.first()
        if config:
            return config.batch_size
    except Exception:
        pass

    return 20  # Default


# ========================================
# Teams Configuration
# ========================================

def get_teams_tenant() -> str:
    """
    Obtiene el Tenant ID de Azure AD para Teams.

    Orden de prioridad:
    1. Configuración en base de datos (si existe y no está vacía)
    2. Variable de entorno TEAMS_TENANT
    3. Default: string vacío

    Returns:
        str: Tenant ID de Azure AD
    """
    try:
        from alumnos.models import Configuracion
        config = Configuracion.objects.first()
        if config and config.teams_tenant_id:
            return config.teams_tenant_id
    except Exception:
        pass

    return getattr(settings, 'TEAMS_TENANT', '')


def get_teams_client_id() -> str:
    """
    Obtiene el Client ID de Teams App.

    Orden de prioridad:
    1. Configuración en base de datos (si existe y no está vacía)
    2. Variable de entorno TEAMS_CLIENT_ID
    3. Default: string vacío

    Returns:
        str: Client ID de Teams App
    """
    try:
        from alumnos.models import Configuracion
        config = Configuracion.objects.first()
        if config and config.teams_client_id:
            return config.teams_client_id
    except Exception:
        pass

    return getattr(settings, 'TEAMS_CLIENT_ID', '')


def get_teams_client_secret() -> str:
    """
    Obtiene el Client Secret de Teams App.

    Orden de prioridad:
    1. Configuración en base de datos (si existe y no está vacía)
    2. Variable de entorno TEAMS_CLIENT_SECRET
    3. Default: string vacío

    Returns:
        str: Client Secret de Teams App
    """
    try:
        from alumnos.models import Configuracion
        config = Configuracion.objects.first()
        if config and config.teams_client_secret:
            return config.teams_client_secret
    except Exception:
        pass

    return getattr(settings, 'TEAMS_CLIENT_SECRET', '')


def get_account_prefix() -> str:
    """
    Obtiene el prefijo para cuentas de usuario.

    Orden de prioridad:
    1. Configuración en base de datos (si existe y no está vacía)
    2. Variable de entorno ACCOUNT_PREFIX
    3. Default: 'test-a' (para ambientes de testing)

    Returns:
        str: Prefijo de cuentas (ej: 'test-a' o 'a')
    """
    try:
        from alumnos.models import Configuracion
        config = Configuracion.objects.first()
        if config and config.account_prefix:
            return config.account_prefix
    except Exception:
        pass

    return getattr(settings, 'ACCOUNT_PREFIX', 'test-a')


# ========================================
# Email Configuration
# ========================================

def get_email_from() -> str:
    """
    Obtiene el email remitente para notificaciones.

    Orden de prioridad:
    1. Configuración en base de datos (si existe y no está vacía)
    2. Variable de entorno DEFAULT_FROM_EMAIL
    3. Default: 'no-reply@eco.unrc.edu.ar'

    Returns:
        str: Email remitente
    """
    try:
        from alumnos.models import Configuracion
        config = Configuracion.objects.first()
        if config and config.email_from:
            return config.email_from
    except Exception:
        pass

    return getattr(settings, 'DEFAULT_FROM_EMAIL', 'no-reply@eco.unrc.edu.ar')


def get_email_host() -> str:
    """
    Obtiene el servidor SMTP para envío de emails.

    Orden de prioridad:
    1. Configuración en base de datos (si existe y no está vacía)
    2. Variable de entorno EMAIL_HOST
    3. Default: 'mailhog' (para testing con Docker)

    Returns:
        str: Servidor SMTP
    """
    try:
        from alumnos.models import Configuracion
        config = Configuracion.objects.first()
        if config and config.email_host:
            return config.email_host
    except Exception:
        pass

    return getattr(settings, 'EMAIL_HOST', 'mailhog')


def get_email_port() -> int:
    """
    Obtiene el puerto SMTP para envío de emails.

    Orden de prioridad:
    1. Configuración en base de datos (si existe y no es NULL)
    2. Variable de entorno EMAIL_PORT
    3. Default: 1025 (puerto de MailHog para testing)

    Returns:
        int: Puerto SMTP
    """
    try:
        from alumnos.models import Configuracion
        config = Configuracion.objects.first()
        if config and config.email_port is not None:
            return config.email_port
    except Exception:
        pass

    return int(getattr(settings, 'EMAIL_PORT', 1025))


def get_email_use_tls() -> bool:
    """
    Determina si se debe usar TLS para conexión SMTP.

    Orden de prioridad:
    1. Configuración en base de datos (si existe y no es NULL)
    2. Variable de entorno EMAIL_USE_TLS
    3. Default: False (MailHog no usa TLS)

    Returns:
        bool: True si se debe usar TLS
    """
    try:
        from alumnos.models import Configuracion
        config = Configuracion.objects.first()
        if config and config.email_use_tls is not None:
            return config.email_use_tls
    except Exception:
        pass

    return getattr(settings, 'EMAIL_USE_TLS', False)


def get_moodle_email_type() -> str:
    """
    Obtiene el tipo de email a usar para enrollment en Moodle.

    Orden de prioridad:
    1. Configuración en base de datos (si existe)
    2. Default: 'institucional'

    Returns:
        str: 'institucional' o 'personal'
    """
    try:
        from alumnos.models import Configuracion
        config = Configuracion.objects.first()
        if config and config.moodle_email_type:
            return config.moodle_email_type
    except Exception:
        pass

    return 'institucional'


def get_moodle_student_roleid() -> int:
    """
    Obtiene el Role ID de estudiante en Moodle.

    Orden de prioridad:
    1. Configuración en base de datos (si existe)
    2. Default: 5 (estándar de Moodle)

    Returns:
        int: Role ID de estudiante
    """
    try:
        from alumnos.models import Configuracion
        config = Configuracion.objects.first()
        if config and config.moodle_student_roleid:
            return config.moodle_student_roleid
    except Exception:
        pass

    return 5
