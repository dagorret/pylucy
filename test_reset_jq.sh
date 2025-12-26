#!/bin/bash

TENANT_ID="1f7d4699-ccd7-45d6-bc78-b8b950bcaedc"
CLIENT_ID="138e98af-33e5-439c-9981-3caaedc65c70"
CLIENT_SECRET="VE~8Q~SbnnIUg-iEHnr1m8nxu5J0RAskpLJPlbuU"
USER="test-a48325621@eco.unrc.edu.ar"
NEWPASS="TestPassword123!"

echo "============================================"
echo "PRUEBA DE RESET PASSWORD CON JQ"
echo "============================================"
echo ""

# 1. Obtener token
TOKEN=$(curl -s -X POST "https://login.microsoftonline.com/${TENANT_ID}/oauth2/v2.0/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "client_id=${CLIENT_ID}" \
  -d "client_secret=${CLIENT_SECRET}" \
  -d "grant_type=client_credentials" \
  -d "scope=https://graph.microsoft.com/.default" \
| jq -r '.access_token')

echo "TOKEN len=${#TOKEN}"
echo ""

# 2. Obtener usuario
echo "Obteniendo usuario..."
curl -s -X GET "https://graph.microsoft.com/v1.0/users/${USER}?\$select=id,userPrincipalName" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
| jq

echo ""
echo "============================================"
echo "Intentando resetear password..."
echo "============================================"
echo ""

# 3. Resetear password
curl -i -X PATCH "https://graph.microsoft.com/v1.0/users/${USER}" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "passwordProfile": {
      "password": "'"${NEWPASS}"'",
      "forceChangePasswordNextSignIn": true
    }
  }'

echo ""
echo "============================================"
