from django.utils import timezone

from .models import Alumno
from .services import actualizar_estado_alumno
from .uti_client import (
    fetch_preinscriptos,
    fetch_ingresantes,
    fetch_aspirantes,
    fetch_detalle_alumno,
)

def obtener_o_crear_alumno_desde_datos(d: dict) -> Alumno:
    """
    Mapea el JSON de la lista (preinscriptos/ingresantes/aspirantes)
    al modelo Alumno.

    Estrategia:
      1) Buscar Alumno por dni.
      2) Si existe → lo devolvemos tal cual.
      3) Si NO existe → llamamos a fetch_detalle_alumno(dni)
         y creamos el Alumno con tipodoc, nombre, apellido, etc.
    """
    dni = d["nrodoc"]

    # 1) Si ya existe, lo devolvemos
    try:
        alumno = Alumno.objects.get(dni=dni)
        return alumno
    except Alumno.DoesNotExist:
        pass

    # 2) No existe → pedimos los datos personales a la API UTI (mock)
    detalle = fetch_detalle_alumno(dni)

    # La API devuelve una lista con un solo objeto, ej:
    # [{
    #   "tipodoc":"DNI","nrodoc":"16953131",
    #   "nombre":"Nxs","apellido":"Ohtz",
    #   "email":"...","fecha_natal":"25/02/91",
    #   "telefono":"...","localidad":"Río Cuarto"
    # }]
    if isinstance(detalle, list) and detalle:
        detalle = detalle[0]

    tipodoc = (detalle.get("tipodoc") or "DNI")[:10]
    nrodoc_str = detalle.get("nrodoc") or str(dni)
    nrodoc_int = int(nrodoc_str)

    nombre = (detalle.get("nombre") or "").strip()[:150]
    apellido = (detalle.get("apellido") or "").strip()[:150]
    email = (detalle.get("email") or "").strip()
    localidad = (detalle.get("localidad") or "").strip()[:150]
    telefono = (detalle.get("telefono") or "").strip()[:50]

    # ⚠ nombre y apellido NO permiten blank=True.
    # Si vinieran vacíos (mock muy raro), ponemos algo mínimo.
    if not nombre:
        nombre = "SIN NOMBRE"
    if not apellido:
        apellido = "SIN APELLIDO"

    alumno = Alumno.objects.create(
        tipodoc=tipodoc,
        dni=nrodoc_int,
        nombre=nombre,
        apellido=apellido,
        email=email,
        localidad=localidad,
        telefono=telefono,
        # modalidad la dejamos en None por ahora
    )
    return alumno

def _rango_por_defecto(desde, hasta):
    if desde is not None and hasta is not None:
        return desde, hasta
    hoy = timezone.now().date()
    return hoy, hoy


def sync_listado_preinscriptos(desde=None, hasta=None, n: int | None = None):
    desde, hasta = _rango_por_defecto(desde, hasta)
    datos = fetch_preinscriptos(desde, hasta, n=n)
    for item in datos:
        alumno = obtener_o_crear_alumno_desde_datos(item)
        actualizar_estado_alumno(alumno, "preinscripto")


def sync_listado_ingresantes(desde=None, hasta=None, n: int | None = None):
    desde, hasta = _rango_por_defecto(desde, hasta)
    datos = fetch_ingresantes(desde, hasta, n=n)
    for item in datos:
        alumno = obtener_o_crear_alumno_desde_datos(item)
        actualizar_estado_alumno(alumno, "ingresante")


def sync_listado_aspirantes(desde=None, hasta=None, n: int | None = None):
    desde, hasta = _rango_por_defecto(desde, hasta)
    datos = fetch_aspirantes(desde, hasta, n=n)
    for item in datos:
        alumno = obtener_o_crear_alumno_desde_datos(item)
        actualizar_estado_alumno(alumno, "aspirante")

