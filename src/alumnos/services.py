import datetime
from typing import Dict, List, Optional, Tuple

import requests
from django.conf import settings

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
) -> Dict:
    """Arma los defaults para update_or_create de Alumno."""
    carreras = lista_item.get("carreras") or []
    carrera_primaria = carreras[0] if carreras else {}
    cohorte = carrera_primaria.get("cohorte")
    modalidad = carrera_primaria.get("modalidad")
    fecha_inscri = carrera_primaria.get("fecha_inscri")

    return {
        "nombre": (personal.get("nombre") or "").strip(),
        "apellido": (personal.get("apellido") or "").strip(),
        "email_personal": (personal.get("email") or "").strip(),
        "fecha_nacimiento": _parse_fecha_natal(personal.get("fecha_natal")),
        "cohorte": cohorte if cohorte is not None else None,
        "localidad": personal.get("localidad") or None,
        "telefono": personal.get("telefono") or None,
        "email_institucional": personal.get("email_institucional") or None,
        "estado_actual": tipo_estado,
        "fecha_ingreso": _parse_fecha_inscri(fecha_inscri),
        "estado_ingreso": carrera_primaria.get("estado_ingreso") or None,
        "modalidad_actual": (modalidad or "").strip() or None,
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

        if nrodoc not in cache_personal:
            try:
                cache_personal[nrodoc] = client.fetch_datospersonales(nrodoc)
            except Exception as exc:
                errors.append(f"{tipodoc} {nrodoc}: error datospersonales ({exc})")
                cache_personal[nrodoc] = {}

        defaults = _build_defaults(tipo, item, cache_personal.get(nrodoc, {}))
        try:
            obj, is_created = Alumno.objects.update_or_create(
                tipo_documento=tipodoc, dni=nrodoc, defaults=defaults
            )
            created += 1 if is_created else 0
            updated += 0 if is_created else 1
        except Exception as exc:
            errors.append(f"{tipodoc} {nrodoc}: error al guardar ({exc})")

    return created, updated, errors
