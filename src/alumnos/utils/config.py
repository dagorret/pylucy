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

    Por ahora solo lee de variables de entorno.
    Podría extenderse para leer de BD en el futuro.

    Returns:
        str: URL base de SIAL/UTI
    """
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
