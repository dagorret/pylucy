"""
Nombre del Módulo: services_old.py

Descripción:
Servicios legacy (versión anterior).

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
import datetime
import secrets
import string
from typing import Dict, List, Optional, Tuple

import requests
from django.conf import settings

from cursos.services import resolver_curso
from .models import Alumno


class SIALClient:
    """Cliente HTTP simple para la API SIAL/UTI (mock o prod)."""

    def __init__(self, base_url: str = None, user: str = None, password: str = None):
        self.base_url = (base_url or settings.SIAL_BASE_URL).rstrip("/")
        self.auth = (user or settings.SIAL_BASIC_USER, password or settings.SIAL_BASIC_PASS)
        self.session = requests.Session()
        self.session.auth = self.auth

    def fetch_listas(
        self,
        tipo: str,
        n: Optional[int] = None,
        fecha: Optional[str] = None,
        desde: Optional[str] = None,
        hasta: Optional[str] = None,
        seed: Optional[int] = None,
    ) -> List[dict]:
        """
        Llama a /listas/ (completa), /listas/{fecha} o /listas/{desde}/{hasta} según parámetros.
        """
        path = f"/webservice/sial/V2/04/{tipo}/listas"
        if fecha:
            path += f"/{fecha}"
        elif desde and hasta:
            path += f"/{desde}/{hasta}"
        else:
            path += "/"

        params = {}
        if n is not None:
            params["n"] = n
        if seed is not None:
            params["seed"] = seed

        url = self.base_url + path
        resp = self.session.get(url, params=params, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def fetch_datospersonales(self, nrodoc: str) -> dict:
        """
        Llama a /alumnos/datospersonales/{nrodoc} y devuelve el primer registro.
        """
        path = f"/webservice/sial/V2/04/alumnos/datospersonales/{nrodoc}"
        url = self.base_url + path
        resp = self.session.get(url, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        return data[0] if data else {}


def _parse_fecha_natal(fecha_natal: Optional[str]) -> Optional[datetime.date]:
    if not fecha_natal:
        return None
    try:
        return datetime.datetime.strptime(fecha_natal.strip(), "%d/%m/%y").date()
    except Exception:
        return None


def _parse_fecha_inscri(fecha_inscri: Optional[str]) -> Optional[datetime.date]:
    if not fecha_inscri:
        return None
    for fmt in ("%d/%m/%Y %H:%M:%S", "%d/%m/%Y"):
        try:
            return datetime.datetime.strptime(fecha_inscri.strip(), fmt).date()
        except Exception:
            continue
    return None


def _build_defaults(
    tipo_estado: str,
    lista_item: dict,
    personal: dict,
    existing: Optional[Alumno],
) -> Dict:
    """
    Arma los defaults para update_or_create de Alumno.
    Implementa lógica de evolución: solo avanza estados, nunca retrocede.
    """
    # Jerarquía de estados (de menor a mayor)
    JERARQUIA_ESTADOS = {
        "preinscripto": 1,
        "aspirante": 2,
        "ingresante": 3,
        "alumno": 4,
    }

    estado_map = {
        "preinscriptos": "preinscripto",
        "aspirantes": "aspirante",
        "ingresantes": "ingresante",
    }
    estado_nuevo = estado_map.get(tipo_estado, tipo_estado)

    # Determinar el estado final según evolución
    if existing and existing.estado_actual:
        estado_actual = existing.estado_actual
        nivel_actual = JERARQUIA_ESTADOS.get(estado_actual, 0)
        nivel_nuevo = JERARQUIA_ESTADOS.get(estado_nuevo, 0)

        # Solo evolucionar si el nuevo estado es superior
        if nivel_nuevo > nivel_actual:
            estado_normalizado = estado_nuevo
        else:
            # Mantener el estado actual (no retroceder)
            estado_normalizado = estado_actual
    else:
        # Alumno nuevo, usar el estado que viene
        estado_normalizado = estado_nuevo
    carreras = lista_item.get("carreras") or []
    carrera_primaria = carreras[0] if carreras else {}
    cohorte = carrera_primaria.get("cohorte")
    modalidad = carrera_primaria.get("modalidad")
    fecha_inscri = carrera_primaria.get("fecha_inscri")
    modalidad_normalizada = (modalidad or "").strip() or None

    def _gen_password(length: int = 16) -> str:
        alphabet = string.ascii_letters + string.digits
        return "".join(secrets.choice(alphabet) for _ in range(length))

    nrodoc = str(lista_item.get("nrodoc") or "").strip()
    # Usar prefijo según modo (#ETME: test-a en testing, a en producción)
    upn = f"{settings.ACCOUNT_PREFIX}{nrodoc}@eco.unrc.edu.ar" if nrodoc else None
    email_inst = upn or (personal.get("email_institucional") or "").strip() or None

    teams_password = existing.teams_password if existing and existing.teams_password else _gen_password()

    email_payload = {
        "metadata": {"origen": "sial-mock", "tipo": estado_normalizado},
        "email": {
            "from": "no-reply@eco.unrc.edu.ar",
            "server": "smtp.eco.unrc.edu.ar",
            "to": email_inst or personal.get("email") or "",
        },
        "api": {
            "enviar": "smtp.eco.unrc.edu.ar:587"
        },
    }

    teams_payload = {
        "auth": {
            "tenant": settings.TEAMS_TENANT,
            "client_id": settings.TEAMS_CLIENT_ID or "TEAMS_CLIENT_ID_PLACEHOLDER",
            "client_secret": settings.TEAMS_CLIENT_SECRET or "TEAMS_CLIENT_SECRET_PLACEHOLDER",
        },
        "usuario": {
            "upn": upn,
            "display_name": f"{personal.get('apellido', '')}, {personal.get('nombre', '')}".strip(", "),
            "password": teams_password,
        },
        "acciones": ["buscar_usuario", "crear_si_no_existe", "asignar_licencia"],
        "api": {
            "buscar_usuario": "https://graph.microsoft.com/v1.0/users/{upn}",
            "crear_usuario": "https://graph.microsoft.com/v1.0/users",
            "asignar_licencia": "https://graph.microsoft.com/v1.0/users/{id}/licenseDetails",
        },
    }

    def _resolver_cursos() -> List[str]:
        shortnames: List[str] = []
        for carrera in carreras:
            id_carrera = carrera.get("id_carrera")
            comisiones = carrera.get("comisiones") or []
            modalidad_carrera = (carrera.get("modalidad") or "").strip()
            comision = None
            if comisiones:
                comision = str(comisiones[0].get("id_comision") or "").strip() or None
            try:
                cursos = resolver_curso(str(id_carrera), modalidad_carrera, comision)
                # Ahora resolver_curso devuelve List[str], extender la lista con todos los cursos
                shortnames.extend(cursos)
            except Exception:
                continue
        return shortnames

    moodle_courses = _resolver_cursos()
    moodle_payload = {
        "auth": {
            "domain": settings.MOODLE_BASE_URL,
            "user": "moodle_api_user",
            "password": "moodle_api_pass",
            "token": settings.MOODLE_WSTOKEN or "MOODLE_TOKEN_PLACEHOLDER",
        },
        "usuario": {
            "username": upn,
            "email": email_inst or personal.get("email") or "",
            "login_via": "microsoft_teams",
        },
        "acciones": {
            "enrolar": {"courses": moodle_courses},
            "enviar_correo_enrolamiento": True,
        },
        "api": {
            "crear_usuario": "https://moodle.eco.unrc.edu.ar/webservice/rest/server.php?wsfunction=core_user_create_users",
            "enrolar_usuario": "https://moodle.eco.unrc.edu.ar/webservice/rest/server.php?wsfunction=enrol_manual_enrol_users",
            "enviar_correo_enrolamiento": "https://moodle.eco.unrc.edu.ar/webservice/rest/server.php?wsfunction=local_send_email",
        },
    }

    return {
        "nombre": (personal.get("nombre") or "").strip(),
        "apellido": (personal.get("apellido") or "").strip(),
        "email_personal": (personal.get("email") or "").strip(),
        "fecha_nacimiento": _parse_fecha_natal(personal.get("fecha_natal")),
        "cohorte": cohorte if cohorte is not None else None,
        "localidad": personal.get("localidad") or None,
        "telefono": personal.get("telefono") or None,
        "email_institucional": personal.get("email_institucional") or None,
        "estado_actual": estado_normalizado,
        "fecha_ingreso": _parse_fecha_inscri(fecha_inscri),
        "estado_ingreso": carrera_primaria.get("estado_ingreso") or None,
        "modalidad_actual": modalidad_normalizada,
        "teams_password": teams_password,
        "teams_payload": teams_payload,
        "email_payload": email_payload,
        "moodle_payload": moodle_payload,
    }


def ingerir_desde_sial(
    tipo: str,
    n: Optional[int] = None,
    fecha: Optional[str] = None,
    desde: Optional[str] = None,
    hasta: Optional[str] = None,
    seed: Optional[int] = None,
    client: Optional[SIALClient] = None,
) -> Tuple[int, int, List[str]]:
    """
    Consume listas SIAL y persiste en Alumno.
    Retorna (creados, actualizados, errores).
    """
    client = client or SIALClient()
    created = 0
    updated = 0
    errors: List[str] = []
    cache_personal: Dict[str, dict] = {}

    try:
        listas = client.fetch_listas(tipo, n=n, fecha=fecha, desde=desde, hasta=hasta, seed=seed)
    except Exception as exc:
        errors.append(f"Error al consultar listas: {exc}")
        return created, updated, errors

    for item in listas:
        tipodoc = item.get("tipodoc") or "DNI"
        nrodoc = str(item.get("nrodoc") or "").strip()
        if not nrodoc:
            errors.append("Registro sin nrodoc")
            continue
        existing = Alumno.objects.filter(tipo_documento=tipodoc, dni=nrodoc).first()
        if nrodoc not in cache_personal:
            try:
                cache_personal[nrodoc] = client.fetch_datospersonales(nrodoc)
            except Exception as exc:
                errors.append(f"{tipodoc} {nrodoc}: error datospersonales ({exc})")
                cache_personal[nrodoc] = {}

        defaults = _build_defaults(tipo, item, cache_personal.get(nrodoc, {}), existing)
        try:
            obj, is_created = Alumno.objects.update_or_create(
                tipo_documento=tipodoc, dni=nrodoc, defaults=defaults
            )
            created += 1 if is_created else 0
            updated += 0 if is_created else 1
        except Exception as exc:
            errors.append(f"{tipodoc} {nrodoc}: error al guardar ({exc})")

    return created, updated, errors
