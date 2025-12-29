"""
Nombre del Módulo: utils.py

Descripción:
Utilidades para la aplicación Cursos.
Funciones auxiliares para obtener información de carreras por ID de UTI.

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
