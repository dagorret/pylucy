#!/usr/bin/env python
"""
Script de prueba simple para resetear password en Teams/Azure AD.
Prueba directamente la API sin Django.
"""
import requests
import string
import secrets
from urllib.parse import quote

# Configuración (copiada del .env)
TEAMS_TENANT = "1f7d4699-ccd7-45d6-bc78-b8b950bcaedc"
TEAMS_CLIENT_ID = "138e98af-33e5-439c-9981-3caaedc65c70"
TEAMS_CLIENT_SECRET = "VE~8Q~SbnnIUg-iEHnr1m8nxu5J0RAskpLJPlbuU"
ACCOUNT_PREFIX = "a"

BASE_URL = "https://graph.microsoft.com/v1.0"

def get_access_token():
    """Obtiene token de acceso de Azure AD."""
    url = f"https://login.microsoftonline.com/{TEAMS_TENANT}/oauth2/v2.0/token"
    data = {
        "client_id": TEAMS_CLIENT_ID,
        "client_secret": TEAMS_CLIENT_SECRET,
        "scope": "https://graph.microsoft.com/.default",
        "grant_type": "client_credentials"
    }
    response = requests.post(url, data=data, timeout=10)
    response.raise_for_status()
    return response.json()["access_token"]

def generate_temp_password(dni: str) -> str:
    """Genera contraseña temporal basada en DNI."""
    alphabet = string.ascii_letters + string.digits
    random_suffix = ''.join(secrets.choice(alphabet) for _ in range(6))
    return f"{dni}{random_suffix}!"

def reset_password(upn: str):
    """
    Resetea password con URL encoding.
    """
    print(f"\n{'='*60}")
    print(f"PRUEBA: Resetear password para {upn}")
    print(f"{'='*60}\n")

    # Mostrar UPN codificado
    upn_encoded = quote(upn, safe='')
    print(f"UPN original: {upn}")
    print(f"UPN codificado: {upn_encoded}\n")

    # Generar password
    dni = upn.split('@')[0].replace(ACCOUNT_PREFIX, '').replace('test-', '')
    new_password = generate_temp_password(dni)
    print(f"Nueva password generada: {new_password}\n")

    # Obtener token
    print("Obteniendo token de acceso...")
    try:
        token = get_access_token()
        print("✅ Token obtenido\n")
    except Exception as e:
        print(f"❌ Error obteniendo token: {e}")
        return False

    # Construir URL y payload
    url = f"{BASE_URL}/users/{upn_encoded}"
    data = {
        "passwordProfile": {
            "forceChangePasswordNextSignIn": True,
            "password": new_password
        }
    }

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    print(f"URL de la petición: {url}")
    print(f"Método: PATCH")
    print(f"Payload: {data}\n")

    # Hacer petición
    try:
        print("Enviando petición PATCH...")
        response = requests.patch(url, json=data, headers=headers, timeout=10)

        print(f"Status code: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}\n")

        if response.status_code == 204:
            print(f"✅ PASSWORD RESETEADA EXITOSAMENTE")
            print(f"Nueva password: {new_password}")
            print(f"\nEl usuario deberá cambiar la password en el próximo login.")
            return True
        else:
            print(f"Response body: {response.text}")
            response.raise_for_status()
            return False

    except requests.exceptions.HTTPError as e:
        print(f"❌ ERROR HTTP: {e}")
        print(f"Response body: {e.response.text if e.response else 'N/A'}")
        return False
    except Exception as e:
        print(f"❌ EXCEPCIÓN: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    upn = "test-a48325621@eco.unrc.edu.ar"
    success = reset_password(upn)

    print(f"\n{'='*60}")
    if success:
        print("RESULTADO: ✅ ÉXITO")
    else:
        print("RESULTADO: ❌ FALLO")
    print(f"{'='*60}\n")
