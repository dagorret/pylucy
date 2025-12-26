#!/usr/bin/env python3
import requests
import json
from urllib.parse import quote

TENANT_ID = "1f7d4699-ccd7-45d6-bc78-b8b950bcaedc"
CLIENT_ID = "138e98af-33e5-439c-9981-3caaedc65c70"
CLIENT_SECRET = "VE~8Q~SbnnIUg-iEHnr1m8nxu5J0RAskpLJPlbuU"
UPN = "test-a48325621@eco.unrc.edu.ar"

# Obtener token
print("Obteniendo token...")
url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"
data = {
    "client_id": CLIENT_ID,
    "client_secret": CLIENT_SECRET,
    "scope": "https://graph.microsoft.com/.default",
    "grant_type": "client_credentials"
}

response = requests.post(url, data=data, timeout=10)
response.raise_for_status()
token = response.json()["access_token"]
print(f"✅ Token obtenido\n")

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

# URL encode
upn_encoded = quote(UPN, safe='')

# 1. Verificar si el usuario existe
print("=" * 60)
print(f"VERIFICANDO USUARIO: {UPN}")
print("=" * 60)
print()

get_url = f"https://graph.microsoft.com/v1.0/users/{upn_encoded}"
print(f"GET {get_url}")
print()

response = requests.get(get_url, headers=headers, timeout=10)

if response.status_code == 200:
    user = response.json()
    print(f"✅ Usuario encontrado:")
    print(f"   Display Name: {user.get('displayName')}")
    print(f"   UPN: {user.get('userPrincipalName')}")
    print(f"   ID: {user.get('id')}")
    print(f"   Account Enabled: {user.get('accountEnabled')}")
    print(f"   User Type: {user.get('userType')}")

    # Verificar si es un usuario cloud-only
    if "onPremisesSyncEnabled" in user:
        print(f"   🔄 Sync con AD local: {user.get('onPremisesSyncEnabled')}")
        if user.get('onPremisesSyncEnabled'):
            print("   ⚠️  PROBLEMA: Este usuario está sincronizado con AD local")
            print("      No se puede cambiar password desde Azure AD")
    else:
        print(f"   ☁️  Usuario cloud-only (OK para reset password)")

    print()

    # Intentar actualizar password
    print("=" * 60)
    print("INTENTANDO RESETEAR PASSWORD")
    print("=" * 60)
    print()

    patch_url = f"https://graph.microsoft.com/v1.0/users/{upn_encoded}"
    patch_data = {
        "passwordProfile": {
            "forceChangePasswordNextSignIn": True,
            "password": "NewTestPass123!"
        }
    }

    print(f"PATCH {patch_url}")
    print(f"Payload: {json.dumps(patch_data, indent=2)}")
    print()

    patch_response = requests.patch(patch_url, headers=headers, json=patch_data, timeout=10)

    print(f"Status Code: {patch_response.status_code}")

    if patch_response.status_code == 204:
        print("✅ PASSWORD RESETEADA EXITOSAMENTE")
    elif patch_response.status_code == 403:
        print("❌ ERROR 403: Forbidden")
        error_data = patch_response.json()
        print(json.dumps(error_data, indent=2))
    else:
        print(f"❌ ERROR {patch_response.status_code}")
        try:
            print(json.dumps(patch_response.json(), indent=2))
        except:
            print(patch_response.text)

elif response.status_code == 404:
    print("❌ Usuario NO encontrado")
else:
    print(f"❌ Error obteniendo usuario: {response.status_code}")
    print(response.text)

print()
