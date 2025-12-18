import datetime
import secrets
import string
from typing import Dict, List, Optional, Tuple

import requests
from django.conf import settings

from cursos.services import resolver_curso
from ..models import Alumno  # .. porque ahora estamos en alumnos/services/


class SIALClient:
    """Cliente HTTP simple para la API SIAL/UTI (mock o prod)."""

    def __init__(self, base_url: str = None, user: str = None, password: str = None):
        from ..utils.config import get_sial_base_url, get_sial_basic_user, get_sial_basic_pass
        self.base_url = (base_url or get_sial_base_url()).rstrip("/")
        self.auth = (user or get_sial_basic_user(), password or get_sial_basic_pass())
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

    # Auto-calcular cohorte desde fecha_ingreso si no viene
    if not cohorte and fecha_inscri:
        fecha_parsed = _parse_fecha_inscri(fecha_inscri)
        if fecha_parsed:
            cohorte = fecha_parsed.year

    # 🔧 SOLO generar payloads Teams/Email/Moodle para aspirantes/ingresantes
    # Preinscriptos NO tienen cuenta institucional, solo email personal
    nrodoc = str(lista_item.get("nrodoc") or "").strip()

    upn = None
    email_inst = None
    teams_password = None
    teams_payload = None
    email_payload = None

    # Solo para aspirantes e ingresantes crear cuentas y payloads
    if estado_normalizado in ("aspirante", "ingresante"):
        def _gen_password(length: int = 16) -> str:
            alphabet = string.ascii_letters + string.digits
            return "".join(secrets.choice(alphabet) for _ in range(length))

        from alumnos.utils.config import (
            get_account_prefix,
            get_teams_tenant,
            get_teams_client_id,
            get_teams_client_secret,
            get_email_from,
            get_email_host,
            get_email_port,
        )

        upn = f"{get_account_prefix()}{nrodoc}@eco.unrc.edu.ar" if nrodoc else None
        email_inst = upn or (personal.get("email_institucional") or "").strip() or None
        teams_password = existing.teams_password if existing and existing.teams_password else _gen_password()

        email_host = get_email_host()
        email_port = get_email_port()
        email_payload = {
            "metadata": {"origen": "sial-mock", "tipo": estado_normalizado},
            "email": {
                "from": get_email_from(),
                "server": email_host,
                "to": email_inst or personal.get("email") or "",
            },
            "api": {
                "enviar": f"{email_host}:{email_port}"
            },
        }

        teams_payload = {
            "auth": {
                "tenant": get_teams_tenant(),
                "client_id": get_teams_client_id() or "TEAMS_CLIENT_ID_PLACEHOLDER",
                "client_secret": get_teams_client_secret() or "TEAMS_CLIENT_SECRET_PLACEHOLDER",
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
        from cursos.constants import CARRERAS_DICT
        import re

        shortnames: List[str] = []
        for carrera in carreras:
            id_carrera = carrera.get("id_carrera")
            comisiones = carrera.get("comisiones") or []
            modalidad_carrera = (carrera.get("modalidad") or "").strip()
            comision = None

            # Extraer número de comisión desde nombre_comision (ej: "COMISION 1" -> "1")
            if comisiones:
                nombre_comision = comisiones[0].get("nombre_comision", "")
                # Buscar patrón "COMISION X" o "COMISIÓN X" y extraer el número
                match = re.search(r'COMISI[OÓ]N\s+(\d+)', nombre_comision, re.IGNORECASE)
                if match:
                    comision = match.group(1)  # Extrae "1", "2", "3", etc.

            # Mapear id_carrera de UTI a código interno (ej: 3 -> CP)
            codigo_carrera = CARRERAS_DICT.get(str(id_carrera)) or CARRERAS_DICT.get(id_carrera)
            if not codigo_carrera:
                continue  # Carrera no reconocida, skip

            try:
                short = resolver_curso(codigo_carrera, modalidad_carrera, comision)
                shortnames.append(short)
            except Exception:
                continue
        return shortnames

    from alumnos.utils.config import get_moodle_base_url, get_moodle_wstoken

    moodle_courses = _resolver_cursos()
    moodle_base_url = get_moodle_base_url()

    # Construir datos de carreras para moodle_payload
    carreras_info = []
    for carrera in carreras:
        import re
        comisiones_list = carrera.get("comisiones") or []
        comision_nombre = comisiones_list[0].get("nombre_comision", "") if comisiones_list else ""

        # Extraer número de comisión
        comision_numero = None
        if comision_nombre:
            match = re.search(r'COMISI[OÓ]N\s+(\d+)', comision_nombre, re.IGNORECASE)
            if match:
                comision_numero = match.group(1)

        carreras_info.append({
            "id_carrera": carrera.get("id_carrera"),
            "modalidad": carrera.get("modalidad"),
            "comision": comision_numero,
            "comision_nombre": comision_nombre,
            "nombre_carrera": carrera.get("nombre_carrera"),
        })

    # Moodle payload solo para aspirantes/ingresantes
    moodle_payload = None
    if estado_normalizado in ("aspirante", "ingresante"):
        moodle_payload = {
            "auth": {
                "domain": moodle_base_url,
                "user": "moodle_api_user",
                "password": "moodle_api_pass",
                "token": get_moodle_wstoken() or "MOODLE_TOKEN_PLACEHOLDER",
            },
            "usuario": {
                "username": upn,
                "email": email_inst or personal.get("email") or "",
                "login_via": "microsoft_teams",
            },
            "carreras": carreras_info,  # Datos completos de carrera/modalidad/comisión
            "acciones": {
                "enrolar": {"courses": moodle_courses},
                "enviar_correo_enrolamiento": True,
            },
            "api": {
                "crear_usuario": f"{moodle_base_url}/webservice/rest/server.php?wsfunction=core_user_create_users",
                "enrolar_usuario": f"{moodle_base_url}/webservice/rest/server.php?wsfunction=enrol_manual_enrol_users",
                "enviar_correo_enrolamiento": f"{moodle_base_url}/webservice/rest/server.php?wsfunction=local_send_email",
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
        "carreras_data": carreras if carreras else None,  # Guardar array completo de carreras
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
    retornar_nuevos: bool = False,
    enviar_email: bool = False,
) -> Tuple[int, int, List[str], Optional[List[int]]]:
    """
    Consume listas SIAL y persiste en Alumno.

    Args:
        tipo: Tipo de ingesta (preinscriptos, aspirantes, ingresantes)
        retornar_nuevos: Si es True, retorna lista de IDs de alumnos creados
        enviar_email: Si es True, envía email de bienvenida a alumnos nuevos

    Returns:
        (creados, actualizados, errores, [nuevos_ids] si retornar_nuevos=True)
    """
    client = client or SIALClient()
    created = 0
    updated = 0
    errors: List[str] = []
    nuevos_ids: List[int] = [] if retornar_nuevos else None
    cache_personal: Dict[str, dict] = {}

    try:
        listas = client.fetch_listas(tipo, n=n, fecha=fecha, desde=desde, hasta=hasta, seed=seed)
    except Exception as exc:
        errors.append(f"Error al consultar listas: {exc}")
        if retornar_nuevos:
            return created, updated, errors, nuevos_ids
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

            # Si es nuevo y se solicitan IDs, agregarlo a la lista
            if is_created and retornar_nuevos:
                nuevos_ids.append(obj.id)

            # Si es nuevo y se solicita envío de email, enviar
            if is_created and enviar_email:
                if obj.email_personal or obj.email_institucional:
                    try:
                        from .email_service import EmailService
                        email_svc = EmailService()
                        email_result = email_svc.send_welcome_email(obj)
                        if not email_result:
                            errors.append(f"{tipodoc} {nrodoc}: error enviando email de bienvenida")
                    except Exception as email_exc:
                        errors.append(f"{tipodoc} {nrodoc}: error enviando email ({email_exc})")
                else:
                    errors.append(f"{tipodoc} {nrodoc}: sin email, no se pudo enviar bienvenida")

        except Exception as exc:
            errors.append(f"{tipodoc} {nrodoc}: error al guardar ({exc})")

    if retornar_nuevos:
        return created, updated, errors, nuevos_ids
    return created, updated, errors
