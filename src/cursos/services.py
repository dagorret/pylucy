from typing import Iterable, List, Tuple

from .models import CursoIngreso, CursoRaro, _normalizar_carreras


class MapeoResult:
    def __init__(self, username: str, course_shortname: str):
        self.username = username
        self.course_shortname = course_shortname


class MapeoError:
    def __init__(self, username: str, codigo_carrera: str, comision: str, motivo: str):
        self.username = username
        self.codigo_carrera = codigo_carrera
        self.comision = comision
        self.motivo = motivo


def resolver_curso(codigo_carrera: str, comision: str) -> str:
    """
    Devuelve el shortname de Moodle para la carrera+comisión.
    Prioridad: CursoRaro -> CursoIngreso. Lanza ValueError si no hay match.
    """
    carrera = (codigo_carrera or "").strip().upper()
    com = (comision or "").strip()
    if not carrera:
        raise ValueError("Carrera vacía")

    # Curso raro
    raro = CursoRaro.objects.filter(
        activo=True, comision=com, carreras__contains=[carrera]
    ).first()
    if raro:
        return raro.curso_moodle

    # Curso normal
    normal = CursoIngreso.objects.filter(activo=True, carreras__contains=[carrera]).first()
    if normal:
        return normal.curso_moodle

    raise ValueError("No se encontró mapeo")


def mapear_lote(alumnos: Iterable[dict], carreras_dict: dict) -> Tuple[List[MapeoResult], List[MapeoError]]:
    """
    Procesa un lote de alumnos (dicts con id_carrera, comision, username).
    Retorna (enrolamientos_ok, errores).
    """
    ok: List[MapeoResult] = []
    errores: List[MapeoError] = []

    for alumno in alumnos:
        username = alumno.get("username") or alumno.get("email") or ""
        id_carrera = alumno.get("id_carrera")
        comision = alumno.get("comision", "")

        carrera_codigo = carreras_dict.get(str(id_carrera)) or carreras_dict.get(id_carrera)
        if not carrera_codigo:
            errores.append(
                MapeoError(username, str(id_carrera), comision, "Carrera no encontrada en diccionario")
            )
            continue

        try:
            course = resolver_curso(carrera_codigo, comision)
            ok.append(MapeoResult(username=username, course_shortname=course))
        except ValueError as exc:
            errores.append(MapeoError(username, carrera_codigo, comision, str(exc)))

    return ok, errores
