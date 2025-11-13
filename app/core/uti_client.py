# core/uti_client.py
#
# Cliente de la API UTI (mock o real).
# Encapsula:
#   - Construcción de URLs (base + path)
#   - Formato de fechas AAAAMMDDHHMM
#   - Autenticación HTTP Basic
#   - Endpoints de listas (preinscriptos, ingresantes, aspirantes)
#   - Endpoint de datos personales por nrodoc
#
# IMPORTANTE:
#   - No debe haber lógica de negocio acá. Solo "hablar" HTTP.
#   - Toda lógica de Alumno (crear/actualizar) va en uti_ingesta.py
#

from datetime import datetime, date
import requests
from django.conf import settings

# Tuplas (user, pass) para HTTP Basic Auth, leídas desde settings.py,
# que a su vez las toma de variables de entorno (UTI_API_USER / UTI_API_PASS).
AUTH = (settings.UTI_API_USER, settings.UTI_API_PASS)


def _build_url(path: str) -> str:
    """
    Construye la URL absoluta concatenando:
        BASE_URL (p.ej. http://localhost:8088)
        +
        path (p.ej. /webservice/sial/V2/04/preinscriptos/listas/...)
    
    - Asegura que no queden dobles barras "//".
    - Si BASE_URL trae barra final o el path viene con barra inicial,
      lo corrige.
    """
    base = settings.UTI_API_BASE_URL.rstrip("/")  # quita "/" al final
    path = path.lstrip("/")                       # quita "/" al inicio
    return f"{base}/{path}"                       # junta con UNA sola "/"


def _formatear_fecha_aaaammddhhmm(value) -> str:
    """
    Normaliza una fecha al formato de la API UTI: 'AAAAMMDDHHMM'

    Acepta:
      - datetime  → usa tal cual
      - date      → asume hora 00:00
      - str       → si ya viene como 'AAAAMMDDHHMM', la devuelve sin tocar;
                    si viene 'YYYY-MM-DD', intenta parsearla.
    
    Si no entiende el tipo → lanza TypeError.
    Si el string no tiene formato válido → ValueError vía fromisoformat.
    """
    if isinstance(value, datetime):
        dt = value
    elif isinstance(value, date):
        # Si sólo es una fecha, asumimos el comienzo del día (00:00)
        dt = datetime(value.year, value.month, value.day, 0, 0)
    elif isinstance(value, str):
        value = value.strip()
        # Caso 1: ya viene como 'AAAAMMDDHHMM' (12 dígitos numéricos)
        if len(value) == 12 and value.isdigit():
            return value
        # Caso 2: intentamos 'YYYY-MM-DD' o similares compatibles con fromisoformat
        dt = datetime.fromisoformat(value)
    else:
        raise TypeError(f"Tipo de fecha no soportado: {type(value)}")

    # Formato requerido por la UTI/mock: AAAAMMDDHHMM (e.g. 202501011230)
    return dt.strftime("%Y%m%d%H%M")


def _formatear_rango(desde, hasta):
    """
    Helper que toma dos fechas (date/datetime/str) y devuelve
    una tupla de strings (desde_str, hasta_str) en formato AAAAMMDDHHMM.
    """
    return _formatear_fecha_aaaammddhhmm(desde), _formatear_fecha_aaaammddhhmm(hasta)


def _fetch_listas_rango(tipo: str, desde, hasta, n: int | None = None):
    """
    Llama al endpoint genérico de 'listas' en modo RANGO:

        /webservice/sial/V2/04/{tipo}/listas/{desde}/{hasta}

    donde:
      - tipo: 'preinscriptos' | 'aspirantes' | 'ingresantes' (en el mock)
      - desde/hasta: convertidos a AAAAMMDDHHMM
      - n (opcional): parámetro específico del mock que pide "n" resultados
                      (en producción esto no existiría).

    Devuelve:
      - El JSON ya decodificado (list/dict) o levanta excepción HTTP si falla.
    """
    # Normalizamos fechas al formato de la API
    desde_str, hasta_str = _formatear_rango(desde, hasta)

    # Patrón base: "/webservice/sial/V2/04/{tipo}/listas"
    base_pattern = settings.UTI_API_LISTAS_BASE
    # Rellenamos {tipo}, ej: "/webservice/sial/V2/04/preinscriptos/listas"
    path = base_pattern.format(tipo=tipo)
    # Agregamos /{desde}/{hasta}
    path = f"{path}/{desde_str}/{hasta_str}"

    # Parámetros de query (el mock admite 'n' para limitar registros)
    params = {}
    if n is not None:
        params["n"] = n

    # Construimos la URL absoluta
    url = _build_url(path)

    # Hacemos GET con:
    #  - params: querystring
    #  - auth: HTTP Basic (usuario/contraseña)
    #  - timeout: 10s (para evitar colgarse indefinidamente)
    resp = requests.get(url, params=params, auth=AUTH, timeout=10)
    resp.raise_for_status()  # lanza error si el HTTP status no es 2xx

    # Retornamos el JSON ya parseado (list/dict)
    return resp.json()


def fetch_preinscriptos(desde, hasta, n: int | None = None):
    """
    API pública para obtener preinscriptos en un rango de fechas.
    Es la que usará la capa de ingesta.
    """
    return _fetch_listas_rango("preinscriptos", desde, hasta, n=n)


def fetch_ingresantes(desde, hasta, n: int | None = None):
    """
    API pública para obtener ingresantes en un rango de fechas.
    """
    return _fetch_listas_rango("ingresantes", desde, hasta, n=n)


def fetch_aspirantes(desde, hasta, n: int | None = None):
    """
    API pública para obtener aspirantes en un rango de fechas.
    (Tipo soportado en el mock.)
    """
    return _fetch_listas_rango("aspirantes", desde, hasta, n=n)


def fetch_detalle_alumno(nrodoc: int | str):
    """
    Llama al endpoint de datos personales de un alumno por nrodoc:

        /webservice/sial/V2/04/alumnos/datospersonales/{nrodoc}

    - nrodoc: DNI numérico (int o string convertible).
    - Devuelve el JSON con los datos personales simulados.

    Esta función se usará más adelante para:
      - complementar datos de Alumno
      - refrescar datos personales periódicamente
    """
    # Completamos el patrón con el nrodoc:
    # "/webservice/sial/V2/04/alumnos/datospersonales/12345678"
    path = settings.UTI_API_DATOS_PERSONALES.format(nrodoc=nrodoc)
    url = _build_url(path)

    resp = requests.get(url, auth=AUTH, timeout=10)
    resp.raise_for_status()
    return resp.json()

