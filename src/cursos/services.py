"""
Nombre del Módulo: services.py

Descripción:
Servicios de lógica de negocio para la aplicación Cursos.
Incluye resolución de cursos, mapeo de alumnos a cursos de Moodle,
y validación de combinaciones carrera-modalidad-comisión.

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
from typing import Iterable, List, Tuple

from .constants import CARRERAS_DICT, MODALIDADES_DICT
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


def resolver_curso(codigo_carrera: str, modalidad: str, comision: str) -> List[str]:
    """
    Devuelve TODOS los shortnames de Moodle para la combinación carrera + modalidad + comisión.
    Retorna una lista de cursos que coinciden (un alumno puede estar en múltiples materias).
    Prioridad: CursoIngreso con coincidencia exacta de comisión si viene informada.
    Lanza ValueError si no hay match.
    """
    carrera = (codigo_carrera or "").strip().upper()
    com_list = _normalizar_comisiones(comision)

    # Mapear modalidad de UTI (1, 2) a código interno (PRES, DIST)
    mod_raw = (modalidad or "").strip()
    mod = MODALIDADES_DICT.get(mod_raw) or MODALIDADES_DICT.get(int(mod_raw)) if mod_raw.isdigit() else mod_raw.upper()

    if not carrera:
        raise ValueError("Carrera vacía")
    if not mod:
        raise ValueError("Modalidad vacía")

    normales = CursoIngreso.objects.filter(
        activo=True, carreras__contains=[carrera], modalidades__contains=[mod]
    )

    # Si hay comisión especificada, filtrar por ella
    if com_list:
        for com in com_list:
            con_comision = normales.filter(comisiones__contains=[com])
            if con_comision.exists():
                return [c.curso_moodle for c in con_comision]

    # Devolver todos los cursos que coinciden (sin filtro de comisión)
    if normales.exists():
        return [c.curso_moodle for c in normales]

    raise ValueError("No se encontró mapeo")


def mapear_lote(alumnos: Iterable[dict], carreras_dict: dict = None) -> Tuple[List[MapeoResult], List[MapeoError]]:
    """
    Procesa un lote de alumnos (dicts con id_carrera, modalidad, comision, username).
    Retorna (enrolamientos_ok, errores).
    Ahora un alumno puede generar MÚLTIPLES MapeoResult (uno por cada curso que coincida).
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
            cursos = resolver_curso(carrera_codigo, modalidad, comision)
            # Crear un MapeoResult por cada curso que coincida
            for course in cursos:
                ok.append(MapeoResult(username=username, course_shortname=course))
        except ValueError as exc:
            errores.append(MapeoError(username, carrera_codigo, modalidad, comision, str(exc)))

    return ok, errores
