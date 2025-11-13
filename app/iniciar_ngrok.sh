#!/usr/bin/env bash

# ================================
# Script para inicializar Ngrok
# Carga tu authtoken en la máquina
# ================================

echo "🔧 Inicializando configuración de Ngrok..."

read -p "👉 Ingresá tu authtoken de Ngrok: " NGROK_TOKEN

if [[ -z "$NGROK_TOKEN" ]]; then
    echo "❌ Error: no ingresaste un token."
    exit 1
fi

echo "➡️ Ejecutando: ngrok config add-authtoken ********"
ngrok config add-authtoken "$NGROK_TOKEN"

echo "✅ Ngrok quedó configurado correctamente."
echo "   Archivo creado en: ~/.config/ngrok/ngrok.yml"

