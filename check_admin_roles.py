#!/usr/bin/env python3
"""
Verifica si la Service Principal tiene roles administrativos asignados.
Para resetear passwords, puede necesitar el rol "Password Administrator" o "User Administrator".
"""
import requests
import json

TENANT_ID = "1f7d4699-ccd7-45d6-bc78-b8b950bcaedc"
CLIENT_ID = "138e98af-33e5-439c-9981-3caaedc65c70"
CLIENT_SECRET = "VE~8Q~SbnnIUg-iEHnr1m8nxu5J0RAskpLJPlbuU"

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

print("=" * 80)
print("VERIFICANDO ROLES ADMINISTRATIVOS DE LA SERVICE PRINCIPAL")
print("=" * 80)
print()

# 1. Obtener Service Principal
print(f"1. Buscando Service Principal con appId={CLIENT_ID}")
sp_url = f"https://graph.microsoft.com/v1.0/servicePrincipals?$filter=appId eq '{CLIENT_ID}'"
response = requests.get(sp_url, headers=headers, timeout=10)

if response.status_code != 200:
    print(f"❌ Error obteniendo Service Principal: {response.status_code}")
    print(response.text)
    exit(1)

sp_data = response.json()
if not sp_data.get('value'):
    print("❌ Service Principal no encontrada")
    exit(1)

sp = sp_data['value'][0]
sp_id = sp['id']
print(f"   ✅ Service Principal encontrada:")
print(f"      ID: {sp_id}")
print(f"      Display Name: {sp.get('displayName')}")
print()

# 2. Verificar roles asignados
print("2. Verificando roles administrativos asignados...")
roles_url = f"https://graph.microsoft.com/v1.0/servicePrincipals/{sp_id}/appRoleAssignments"
response = requests.get(roles_url, headers=headers, timeout=10)

if response.status_code != 200:
    print(f"❌ Error obteniendo roles: {response.status_code}")
    print(response.text)
else:
    role_assignments = response.json().get('value', [])
    print(f"   Roles asignados: {len(role_assignments)}")

    if role_assignments:
        for assignment in role_assignments:
            print(f"      - Resource: {assignment.get('resourceDisplayName')}")
            print(f"        Role ID: {assignment.get('appRoleId')}")
    else:
        print("   (ninguno)")

print()

# 3. Verificar DIRECTORY ROLES (roles administrativos de Azure AD)
print("3. Verificando Directory Roles (roles de administrador de Azure AD)...")
print()

# Obtener todos los directory roles
directory_roles_url = "https://graph.microsoft.com/v1.0/directoryRoles"
response = requests.get(directory_roles_url, headers=headers, timeout=10)

if response.status_code != 200:
    print(f"❌ Error obteniendo directory roles: {response.status_code}")
else:
    all_roles = response.json().get('value', [])

    # Para cada rol, verificar si nuestra SP es miembro
    sp_roles = []
    for role in all_roles:
        role_id = role['id']
        role_name = role['displayName']

        # Obtener miembros del rol
        members_url = f"https://graph.microsoft.com/v1.0/directoryRoles/{role_id}/members"
        members_response = requests.get(members_url, headers=headers, timeout=10)

        if members_response.status_code == 200:
            members = members_response.json().get('value', [])
            # Verificar si nuestra SP está en los miembros
            for member in members:
                if member.get('id') == sp_id:
                    sp_roles.append(role_name)
                    break

    print(f"   Directory Roles asignados a la Service Principal:")
    if sp_roles:
        for role in sp_roles:
            print(f"      ✓ {role}")
    else:
        print("      ❌ NINGUNO")
        print()
        print("   ⚠️  PROBLEMA DETECTADO:")
        print("      Para resetear passwords, la Service Principal necesita uno de estos roles:")
        print("      - Password Administrator")
        print("      - User Administrator")
        print("      - Privileged Authentication Administrator")
        print()
        print("   SOLUCIÓN:")
        print("   1. Ve a Azure Portal → Azure Active Directory")
        print("   2. Roles and administrators")
        print("   3. Busca 'Password Administrator' o 'User Administrator'")
        print(f"   4. Agrega la aplicación '{sp.get('displayName')}' como miembro del rol")

print()
print("=" * 80)
