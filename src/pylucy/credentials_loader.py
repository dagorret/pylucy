"""
Nombre del Módulo: credentials_loader.py

Descripción:
Módulo para cargar credenciales de servicios externos desde archivos JSON seguros.
Proporciona funciones para leer credenciales de UTI/SIAL, Moodle y Microsoft Teams.

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

import json
import os
from pathlib import Path
from typing import Dict, Optional


# Ruta base del proyecto (raíz donde está la carpeta credenciales/)
BASE_DIR = Path(__file__).resolve().parent.parent.parent
CREDENTIALS_DIR = BASE_DIR / 'credenciales'


def load_json_credentials(filename: str) -> Optional[Dict]:
    """
    Carga credenciales desde un archivo JSON en la carpeta credenciales/.

    Args:
        filename: Nombre del archivo JSON (ej: 'uti_credentials.json')

    Returns:
        Dict con las credenciales o None si el archivo no existe
    """
    filepath = CREDENTIALS_DIR / filename

    if not filepath.exists():
        print(f"⚠️  Archivo de credenciales no encontrado: {filepath}")
        print(f"    Copia {filename}.example y renómbralo a {filename}")
        return None

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"❌ Error al leer {filename}: {e}")
        return None
    except Exception as e:
        print(f"❌ Error inesperado al cargar {filename}: {e}")
        return None


def get_uti_credentials() -> Dict:
    """
    Obtiene credenciales de UTI/SIAL.

    Returns:
        Dict con credenciales o valores por defecto si no están configuradas
    """
    creds = load_json_credentials('uti_credentials.json')

    if creds:
        return {
            'base_url': creds.get('base_url', 'http://localhost:8088'),
            'username': creds.get('basic_auth', {}).get('username', 'usuario'),
            'password': creds.get('basic_auth', {}).get('password', 'contrasena'),
        }

    # Fallback a variables de entorno
    return {
        'base_url': os.getenv('SIAL_BASE_URL', 'http://localhost:8088'),
        'username': os.getenv('SIAL_BASIC_USER', 'usuario'),
        'password': os.getenv('SIAL_BASIC_PASS', 'contrasena'),
    }


def get_moodle_credentials() -> Dict:
    """
    Obtiene credenciales de Moodle.

    Returns:
        Dict con credenciales o valores por defecto si no están configuradas
    """
    creds = load_json_credentials('moodle_credentials.json')

    if creds:
        return {
            'base_url': creds.get('base_url', 'https://sandbox.moodledemo.net'),
            'wstoken': creds.get('wstoken', ''),
            'student_roleid': creds.get('student_roleid', 5),
            'auth_method': creds.get('auth_method', 'oauth2'),
        }

    # Fallback a variables de entorno
    return {
        'base_url': os.getenv('MOODLE_BASE_URL', 'https://sandbox.moodledemo.net'),
        'wstoken': os.getenv('MOODLE_WSTOKEN', ''),
        'student_roleid': int(os.getenv('MOODLE_STUDENT_ROLEID', '5')),
        'auth_method': os.getenv('MOODLE_AUTH_METHOD', 'oauth2'),
    }


def get_teams_credentials() -> Dict:
    """
    Obtiene credenciales de Microsoft Teams / Azure AD.

    Returns:
        Dict con credenciales o valores por defecto si no están configuradas
    """
    creds = load_json_credentials('teams_credentials.json')

    if creds:
        return {
            'tenant_id': creds.get('tenant_id', ''),
            'domain': creds.get('domain', 'ejemplo.com'),
            'client_id': creds.get('client_id', ''),
            'client_secret': creds.get('client_secret', ''),
        }

    # Fallback a variables de entorno
    return {
        'tenant_id': os.getenv('TEAMS_TENANT', ''),
        'domain': os.getenv('TEAMS_DOMAIN', 'ejemplo.com'),
        'client_id': os.getenv('TEAMS_CLIENT_ID', ''),
        'client_secret': os.getenv('TEAMS_CLIENT_SECRET', ''),
    }


def generate_secret_key() -> str:
    """
    Genera una SECRET_KEY segura para Django.

    Returns:
        String con la clave secreta
    """
    from django.core.management.utils import get_random_secret_key
    return get_random_secret_key()


# Cache para evitar leer archivos múltiples veces
_credentials_cache = {}


def get_cached_credentials(service: str) -> Dict:
    """
    Obtiene credenciales con caché para mejorar performance.

    Args:
        service: 'uti', 'moodle' o 'teams'

    Returns:
        Dict con las credenciales
    """
    if service not in _credentials_cache:
        if service == 'uti':
            _credentials_cache[service] = get_uti_credentials()
        elif service == 'moodle':
            _credentials_cache[service] = get_moodle_credentials()
        elif service == 'teams':
            _credentials_cache[service] = get_teams_credentials()
        else:
            raise ValueError(f"Servicio desconocido: {service}")

    return _credentials_cache[service]
