from typing import Iterable, List, Tuple

from .constants import CARRERAS_DICT
from .models import (
    CursoIngreso,
    _normalizar_carreras,
    _normalizar_comisiones,
    _normalizar_modalidades,
)


class MapeoResult:
    def __init__(self, username: str, course_shortname: str):
        self.username = username
        self.course_shortname = course_shortname


class MapeoError:
    def __init__(self, username: str, codigo_carrera: str, modalidad: str, comision: str, motivo: str):
        self.username = username
        self.codigo_carrera = codigo_carrera
        self.modalidad = modalidad
        self.comision = comision
        self.motivo = motivo


def resolver_curso(codigo_carrera: str, modalidad: str, comision: str) -> str:
    """
    Devuelve el shortname de Moodle para la combinación carrera + modalidad + comisión.
    Prioridad: CursoIngreso con coincidencia exacta de comisión si viene informada.
    Lanza ValueError si no hay match.
    """
    carrera = (codigo_carrera or "").strip().upper()
    com_list = _normalizar_comisiones(comision)
    mod = (modalidad or "").strip().upper()
    if not carrera:
        raise ValueError("Carrera vacía")
    if not mod:
        raise ValueError("Modalidad vacía")

    normales = CursoIngreso.objects.filter(
        activo=True, carreras__contains=[carrera], modalidades__contains=[mod]
    )
    for com in com_list:
        normal_con_com = normales.filter(comisiones__contains=[com]).first()
        if normal_con_com:
            return normal_con_com.curso_moodle
    normal = normales.first()
    if normal:
        return normal.curso_moodle

    raise ValueError("No se encontró mapeo")


def mapear_lote(alumnos: Iterable[dict], carreras_dict: dict = None) -> Tuple[List[MapeoResult], List[MapeoError]]:
    """
    Procesa un lote de alumnos (dicts con id_carrera, modalidad, comision, username).
    Retorna (enrolamientos_ok, errores).
    """
    carreras_dict = carreras_dict or CARRERAS_DICT
    ok: List[MapeoResult] = []
    errores: List[MapeoError] = []

    for alumno in alumnos:
        username = alumno.get("username") or alumno.get("email") or ""
        id_carrera = alumno.get("id_carrera")
        comision = alumno.get("comision", "")
        modalidad = alumno.get("modalidad", "")

        carrera_codigo = carreras_dict.get(str(id_carrera)) or carreras_dict.get(id_carrera)
        if not carrera_codigo:
            errores.append(
                MapeoError(username, str(id_carrera), modalidad, comision, "Carrera no encontrada en diccionario")
            )
            continue

        try:
            course = resolver_curso(carrera_codigo, modalidad, comision)
            ok.append(MapeoResult(username=username, course_shortname=course))
        except ValueError as exc:
            errores.append(MapeoError(username, carrera_codigo, modalidad, comision, str(exc)))

    return ok, errores
