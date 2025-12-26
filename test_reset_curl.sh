#!/bin/bash

TENANT_ID="1f7d4699-ccd7-45d6-bc78-b8b950bcaedc"
CLIENT_ID="138e98af-33e5-439c-9981-3caaedc65c70"
CLIENT_SECRET="VE~8Q~SbnnIUg-iEHnr1m8nxu5J0RAskpLJPlbuU"
UPN="test-a48325621@eco.unrc.edu.ar"
NEW_PASSWORD="TestPass123456!"

echo "============================================"
echo "PRUEBA DE RESET PASSWORD CON CURL"
echo "============================================"
echo ""

# 1. Obtener token
echo "1. Obteniendo token de acceso..."
TOKEN=$(curl -s -X POST "https://login.microsoftonline.com/${TENANT_ID}/oauth2/v2.0/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "client_id=${CLIENT_ID}" \
  -d "client_secret=${CLIENT_SECRET}" \
  -d "grant_type=client_credentials" \
  -d "scope=https://graph.microsoft.com/.default" | python3 -c 'import sys, json; print(json.load(sys.stdin)["access_token"])')

echo "   ✅ Token obtenido (length: ${#TOKEN})"
echo ""

# 2. Resetear password
echo "2. Reseteando password para: ${UPN}"
echo "   URL encoding: ${UPN} -> test-a48325621%40eco.unrc.edu.ar"
echo ""

# URL encode del UPN
UPN_ENCODED=$(python3 -c "from urllib.parse import quote; print(quote('${UPN}', safe=''))")

echo "3. Enviando petición PATCH..."
echo "   URL: https://graph.microsoft.com/v1.0/users/${UPN_ENCODED}"
echo ""

RESPONSE=$(curl -s -w "\n%{http_code}" -X PATCH \
  "https://graph.microsoft.com/v1.0/users/${UPN_ENCODED}" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "passwordProfile": {
      "forceChangePasswordNextSignIn": true,
      "password": "'"${NEW_PASSWORD}"'"
    }
  }')

# Separar body y status code
HTTP_BODY=$(echo "$RESPONSE" | head -n -1)
HTTP_CODE=$(echo "$RESPONSE" | tail -n 1)

echo "4. Resultado:"
echo "   Status Code: ${HTTP_CODE}"
echo ""

if [ "$HTTP_CODE" = "204" ]; then
    echo "   ✅ SUCCESS: Password reseteada correctamente"
    echo "   Nueva password: ${NEW_PASSWORD}"
    echo "   El usuario debe cambiarla en el próximo login"
elif [ "$HTTP_CODE" = "403" ]; then
    echo "   ❌ ERROR 403: Insufficient privileges"
    echo "   Response body:"
    echo "$HTTP_BODY" | python3 -m json.tool 2>/dev/null || echo "$HTTP_BODY"
else
    echo "   ❌ ERROR: Status code ${HTTP_CODE}"
    echo "   Response body:"
    echo "$HTTP_BODY" | python3 -m json.tool 2>/dev/null || echo "$HTTP_BODY"
fi

echo ""
echo "============================================"
