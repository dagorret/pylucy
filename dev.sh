#!/usr/bin/env bash
# Script para levantar entorno de DESARROLLO
set -e

echo "🚀 Levantando PyLucy en modo DESARROLLO..."
echo ""

# Levantar servicios
docker compose -f docker-compose.dev.yml up

# Nota: Usa Ctrl+C para detener
