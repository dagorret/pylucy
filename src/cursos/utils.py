"""Utilidades para el módulo cursos."""
from typing import Optional


def get_carrera_by_id_uti(id_uti: int) -> Optional[dict]:
    """
    Obtiene información de la carrera por su ID de UTI.

    Args:
        id_uti: ID de la carrera en la API UTI (ej: 2, 3, 4, 7, 8)

    Returns:
        Dict con {id_uti, codigo, nombre_completo, activo} o None si no existe
    """
    try:
        from .models import Carrera
        carrera = Carrera.objects.filter(id_uti=id_uti, activo=True).first()
        if carrera:
            return {
                "id_uti": carrera.id_uti,
                "codigo": carrera.codigo,
                "nombre_completo": carrera.nombre_completo,
                "activo": carrera.activo,
            }
        return None
    except Exception:
        return None


def get_carrera_nombre(id_uti: int) -> str:
    """
    Obtiene el nombre completo de una carrera por su ID de UTI.

    Args:
        id_uti: ID de la carrera en la API UTI

    Returns:
        Nombre completo de la carrera o "Carrera {id_uti}" si no existe
    """
    carrera = get_carrera_by_id_uti(id_uti)
    if carrera:
        return carrera["nombre_completo"]
    return f"Carrera {id_uti}"


def get_carrera_codigo(id_uti: int) -> Optional[str]:
    """
    Obtiene el código interno de una carrera por su ID de UTI.

    Args:
        id_uti: ID de la carrera en la API UTI

    Returns:
        Código interno (ej: LE, CP, LA) o None si no existe
    """
    carrera = get_carrera_by_id_uti(id_uti)
    if carrera:
        return carrera["codigo"]
    return None
