#!/bin/bash
# Script para sincronizar archivos estáticos entre src/pylucy/static y src/static

echo "Sincronizando archivos estáticos..."

# Copiar de pylucy/static a static (sobrescribir)
rsync -av --delete src/pylucy/static/ src/static/

echo "✅ Archivos sincronizados"
echo ""
echo "Archivos en src/static/:"
ls -la src/static/
