#!/usr/bin/env bash

set -e

cd "$(dirname "$0")"
echo "📁 Directorio actual: $(pwd)"

# 1. Cargar .env si existe
if [ -f .env ]; then
    echo "🔧 Cargando variables desde .env"
    export $(grep -v '^#' .env | xargs)
fi

echo "ENV ➜ DEVEL=$DEVEL"

# 2. Verificar ngrok
if ! command -v ngrok >/dev/null 2>&1; then
    echo "❌ ERROR: ngrok no está instalado."
    echo "Instalalo con: sudo pacman -S ngrok"
    exit 1
fi

# 3. Activar venv
if [ -d .venv ]; then
    echo "🐍 Activando entorno virtual..."
    source .venv/bin/activate
else
    echo "❌ No existe .venv — crealo con: uv venv .venv"
    exit 1
fi

DJANGO_PID=""
PORT=8000

# 4. Chequear si el puerto 8000 ya está en uso
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "⚠️ El puerto $PORT ya está en uso."
    echo "   No voy a lanzar Django, solo Ngrok."
else
    echo "🚀 Iniciando Django en 0.0.0.0:$PORT..."
    uv run python manage.py runserver 0.0.0.0:$PORT &
    DJANGO_PID=$!
    echo "PID Django ➜ $DJANGO_PID"
    sleep 3
fi

# 5. Lanzar Ngrok
echo "🌍 Creando túnel Ngrok hacia http://localhost:$PORT ..."
echo "   (CTRL+C para cortar el túnel)"
ngrok http $PORT

# 6. Si este script lanzó Django, lo matamos al salir
if [ -n "$DJANGO_PID" ]; then
    echo "🛑 Apagando Django (PID $DJANGO_PID)..."
    kill "$DJANGO_PID" 2>/dev/null || true
fi

echo "✨ Todo cerrado correctamente."

