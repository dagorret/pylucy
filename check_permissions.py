#!/usr/bin/env python3
import requests
import base64
import json

TENANT_ID = "1f7d4699-ccd7-45d6-bc78-b8b950bcaedc"
CLIENT_ID = "138e98af-33e5-439c-9981-3caaedc65c70"
CLIENT_SECRET = "VE~8Q~SbnnIUg-iEHnr1m8nxu5J0RAskpLJPlbuU"

# Obtener token
url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"
data = {
    "client_id": CLIENT_ID,
    "client_secret": CLIENT_SECRET,
    "scope": "https://graph.microsoft.com/.default",
    "grant_type": "client_credentials"
}

print("Obteniendo token...")
response = requests.post(url, data=data, timeout=10)
response.raise_for_status()
token = response.json()["access_token"]

print(f"✅ Token obtenido (length: {len(token)})\n")

# Decodificar payload
parts = token.split('.')
payload_encoded = parts[1]

# Agregar padding si es necesario
padding = 4 - (len(payload_encoded) % 4)
if padding != 4:
    payload_encoded += '=' * padding

payload = json.loads(base64.b64decode(payload_encoded))

print("=" * 60)
print("PERMISOS EN EL TOKEN:")
print("=" * 60)
print()

# Permisos requeridos para PyLucy
REQUIRED_PERMISSIONS = {
    'User.ReadWrite.All',
    'UserAuthenticationMethod.ReadWrite.All',
    'User.PasswordProfile.ReadWrite.All',  # ⭐ CRÍTICO para resetear passwords
    'Directory.ReadWrite.All',
    'Group.ReadWrite.All',
    'Mail.Send'
}

# Alias para el permiso de password (Azure lo muestra con guión a veces)
PASSWORD_PROFILE_ALIASES = {
    'User.PasswordProfile.ReadWrite.All',
    'User-PasswordProfile.ReadWrite.All'
}

if "roles" in payload:
    roles = set(payload["roles"])
    print("✓ Roles (Application Permissions):")
    for role in sorted(payload["roles"]):
        # Marcar permisos críticos
        is_password_perm = role in PASSWORD_PROFILE_ALIASES
        marker = " ⭐ CRÍTICO" if is_password_perm else ""
        print(f"  - {role}{marker}")

    print()
    print("=" * 60)
    print("VERIFICACIÓN DE PERMISOS REQUERIDOS:")
    print("=" * 60)
    print()

    # Verificar si tiene alguna variante del permiso de password
    has_password_profile = bool(roles & PASSWORD_PROFILE_ALIASES)

    # Permisos faltantes (excluyendo el permiso de password que tiene alias)
    missing = REQUIRED_PERMISSIONS - roles
    if 'User.PasswordProfile.ReadWrite.All' in missing and has_password_profile:
        # Tiene el permiso con guión, remover de faltantes
        missing.discard('User.PasswordProfile.ReadWrite.All')

    if missing:
        print("❌ FALTAN PERMISOS:")
        for perm in sorted(missing):
            marker = " ⭐ (CRÍTICO)" if perm == 'User.PasswordProfile.ReadWrite.All' else ""
            print(f"  - {perm}{marker}")
        print()
        print("⚠️  Sin estos permisos, el reset de password fallará con 403 Forbidden")
    else:
        print("✅ TODOS LOS PERMISOS REQUERIDOS ESTÁN PRESENTES")

else:
    print("❌ NO HAY ROLES (Application Permissions) EN EL TOKEN")
    print()
    print("Permisos faltantes:")
    for perm in sorted(REQUIRED_PERMISSIONS):
        marker = " ⭐ (CRÍTICO)" if perm == 'User.PasswordProfile.ReadWrite.All' else ""
        print(f"  - {perm}{marker}")

print()

if "scp" in payload:
    print("✓ Scopes (Delegated Permissions):")
    print(f"  {payload['scp']}")
else:
    print("(No hay scopes - esperado para client_credentials)")

print()
print("=" * 60)
print("OTROS DATOS DEL TOKEN:")
print("=" * 60)
print(f"App ID: {payload.get('appid', 'N/A')}")
print(f"Tenant ID: {payload.get('tid', 'N/A')}")
print(f"OID: {payload.get('oid', 'N/A')}")
print()
print("=" * 60)
print("📚 Documentación:")
print("=" * 60)
print("Ver PERMISOS_AZURE_AD.md para más información")
print()
