#!/bin/bash

TENANT_ID="1f7d4699-ccd7-45d6-bc78-b8b950bcaedc"
CLIENT_ID="138e98af-33e5-439c-9981-3caaedc65c70"
CLIENT_SECRET="VE~8Q~SbnnIUg-iEHnr1m8nxu5J0RAskpLJPlbuU"

echo "Obteniendo token..."
TOKEN=$(curl -s -X POST "https://login.microsoftonline.com/${TENANT_ID}/oauth2/v2.0/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "client_id=${CLIENT_ID}" \
  -d "client_secret=${CLIENT_SECRET}" \
  -d "grant_type=client_credentials" \
  -d "scope=https://graph.microsoft.com/.default" | python3 -c 'import sys, json; print(json.load(sys.stdin)["access_token"])')

echo "Token obtenido (length: ${#TOKEN})"
echo ""
echo "============================================"
echo "PERMISOS (ROLES) EN EL TOKEN:"
echo "============================================"
echo ""

# Decodificar el payload del token (parte 2, después del primer punto)
PAYLOAD=$(echo "$TOKEN" | cut -d'.' -f2)

# Agregar padding si es necesario
case $((${#PAYLOAD} % 4)) in
    2) PAYLOAD="${PAYLOAD}==" ;;
    3) PAYLOAD="${PAYLOAD}=" ;;
esac

# Decodificar base64 y extraer roles
echo "$PAYLOAD" | base64 -d 2>/dev/null | python3 << 'PYTHON_SCRIPT'
import sys, json
data = json.load(sys.stdin)
print("Roles (permisos de aplicación):")
if "roles" in data:
    for role in data["roles"]:
        print(f"  ✓ {role}")
else:
    print("  ❌ No hay roles en el token")
print()
print("Scopes (permisos delegados):")
if "scp" in data:
    print(f"  {data['scp']}")
else:
    print("  (ninguno)")
PYTHON_SCRIPT

echo ""
echo "============================================"
