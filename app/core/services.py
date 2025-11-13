# core/services.py
#
# Servicios de dominio de Alumno: manejo de estado_actual.

from .models import AlumnoEstado


# Orden jerárquico de los estados
ORDEN_ESTADO = {
    AlumnoEstado.PREINSCRIPTO: 0,
    AlumnoEstado.ASPIRANTE: 1,
    AlumnoEstado.INGRESANTE: 2,
    AlumnoEstado.ALUMNO: 3,
}


def _estado_desde_origen(desde: str):
    """
    Traduce la fuente del dato a un estado:

      - 'preinscripto'  -> ASPIRANTE
      - 'aspirante'     -> ASPIRANTE
      - 'ingresante'    -> INGRESANTE
      - 'alumno'        -> ALUMNO
    """
    desde = (desde or "").lower()

    if desde == "preinscripto":
        return AlumnoEstado.ASPIRANTE
    if desde == "aspirante":
        return AlumnoEstado.ASPIRANTE
    if desde == "ingresante":
        return AlumnoEstado.INGRESANTE
    if desde == "alumno":
        return AlumnoEstado.ALUMNO
    return None


def actualizar_estado_alumno(alumno, desde: str):
    """
    Actualiza alumno.estado_actual SOLO si el nuevo estado está
    más "avanzado" que el actual, según ORDEN_ESTADO.
    """
    nuevo = _estado_desde_origen(desde)
    if nuevo is None:
        return

    estado_actual = alumno.estado_actual or AlumnoEstado.PREINSCRIPTO

    if ORDEN_ESTADO[nuevo] > ORDEN_ESTADO[estado_actual]:
        alumno.estado_actual = nuevo
        alumno.save(update_fields=["estado_actual"])

