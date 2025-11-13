#!/usr/bin/env bash

# Cargar variables del entorno desde .env si existe
if [ -f .env ]; then
    echo "Cargando variables desde .env"
    export $(grep -v '^#' .env | xargs)
fi

echo "DEVEL=$DEVEL"
echo "Usando UTI_API_BASE_URL=$UTI_API_BASE_URL"

# Arranca el servidor Django con UV
uv run python manage.py runserver

