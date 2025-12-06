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
    """Arma los defaults para update_or_create de Alumno."""
    estado_map = {
        "preinscriptos": "preinscripto",
        "aspirantes": "aspirante",
        "ingresantes": "ingresante",
    }
    estado_normalizado = estado_map.get(tipo_estado, tipo_estado)
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
    upn = f"a{nrodoc}@eco.unrc.edu.ar" if nrodoc else None
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
            "tenant": "eco.unrc.edu.ar",
            "client_id": "TEAMS_CLIENT_ID_PLACEHOLDER",
            "client_secret": "TEAMS_CLIENT_SECRET_PLACEHOLDER",
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
                short = resolver_curso(str(id_carrera), modalidad_carrera, comision)
                shortnames.append(short)
            except Exception:
                continue
        return shortnames

    moodle_courses = _resolver_cursos()
    moodle_payload = {
        "auth": {
            "domain": "https://moodle.eco.unrc.edu.ar",
            "user": "moodle_api_user",
            "password": "moodle_api_pass",
            "token": "MOODLE_TOKEN_PLACEHOLDER",
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
