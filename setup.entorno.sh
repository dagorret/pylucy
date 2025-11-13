#!/usr/bin/env bash
set -e

BASE=~/work/pylucy

echo "======================================================"
echo "  🛠  SETUP DE ENTORNO DJANGO + DOCKER + MOCK API"
echo "======================================================"
echo

# --------------------------------------------------------------------
# 1. Confirmar si ya existe el directorio
# --------------------------------------------------------------------
if [ -d "$BASE" ]; then
    echo "⚠️  El directorio $BASE ya existe."
    read -p "¿Deseas continuar y usarlo igualmente? (s/N): " answer
    if [[ "$answer" != "s" && "$answer" != "S" ]]; then
        echo "❌ Abortado por el usuario."
        exit 1
    fi
fi

# --------------------------------------------------------------------
# 2. Crear estructura de directorios
# --------------------------------------------------------------------
echo "📁 Creando estructura en $BASE ..."
mkdir -p $BASE/{infra,app,ops,docs}

# Mock API (se rellena luego)
mkdir -p $BASE/mock-api-uti

# Estructura de Django
mkdir -p $BASE/app/{core,api,ingest,integrations,templates,static,tests}

# --------------------------------------------------------------------
# 3. Clonar tu mock API
# --------------------------------------------------------------------
echo "🌐 Clonando repo api-mock-lucy ..."
git clone https://github.com/dagorret/api-mock-lucy.git $BASE/mock-api-uti

echo "✔ Mock clonada en: $BASE/mock-api-uti"
echo

# --------------------------------------------------------------------
# 4. Crear archivos base con cat > 
# --------------------------------------------------------------------

echo "📦 Creando archivos base..."

# ---- infra/docker-compose.yml ----
cat > $BASE/infra/docker-compose.yml <<'EOF'
version: "3.9"
services:
  postgres:
    image: postgres:16-alpine
    container_name: dev-postgres
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-app}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-app}
      POSTGRES_DB: ${POSTGRES_DB:-appdb}
    volumes:
      - pgdata:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  pgweb:
    image: sosedoff/pgweb:0.14.0
    container_name: dev-pgweb
    depends_on:
      - postgres
    environment:
      DATABASE_URL: postgres://${POSTGRES_USER:-app}:${POSTGRES_PASSWORD:-app}@postgres:5432/${POSTGRES_DB:-appdb}?sslmode=disable
    ports:
      - "8081:8081"
    command: ["pgweb","--bind=0.0.0.0","--listen=8081"]

  mock-api-uti:
    build:
      context: ../mock-api-uti
      dockerfile: Dockerfile
    container_name: dev-mock-api-uti
    ports:
      - "8090:8090"
    environment:
      SEED_SIZE: "small"

volumes:
  pgdata:
EOF


# ---- infra/.env ----
cat > $BASE/infra/.env <<'EOF'
POSTGRES_USER=app
POSTGRES_PASSWORD=app
POSTGRES_DB=appdb
EOF


# ---- app/pyproject.toml ----
cat > $BASE/app/pyproject.toml <<'EOF'
[project]
name = "lucy-app"
version = "0.1.0"
dependencies = [
  "django>=5.0",
  "djangorestframework",
  "django-filter",
  "psycopg[binary]",
  "django-environ",
  "django-material-admin"
]
[tool.uv]
python = "3.12"
EOF


# ---- app/.env ----
cat > $BASE/app/.env <<'EOF'
DJANGO_DEBUG=1
DB_HOST=localhost
DB_PORT=5432
DB_NAME=appdb
DB_USER=app
DB_PASS=app
EOF


# ---- ops/Makefile ----
cat > $BASE/ops/Makefile <<'EOF'
up:
\tcd ../infra && docker compose up -d

down:
\tcd ../infra && docker compose down

logs:
\tcd ../infra && docker compose logs -f

migrate:
\tcd ../app && uv run python manage.py migrate

run:
\tcd ../app && uv run python manage.py runserver 0.0.0.0:8000

seed:
\tcd ../app && uv run python manage.py seed
EOF


# ---- docs/ARQUITECTURA.txt ----
cat > $BASE/docs/ARQUITECTURA.txt <<'EOF'
Estructura del proyecto:

infra/           -> Docker compose, Postgres, pgweb, Mock API
app/             -> Proyecto Django (código Python)
ops/             -> Scripts, Makefile para automatizar
docs/            -> Documentación técnica
mock-api-uti/    -> API simulada de UTI (clonada del repo GitHub)
EOF


echo "✔ Archivos creados."
echo

# --------------------------------------------------------------------
# 5. Chequeo de dependencias
# --------------------------------------------------------------------
echo "🔎 Verificando dependencias..."

echo "- Docker: $(docker --version || echo 'NO INSTALADO ❌')"
echo "- Docker Compose: $(docker compose version || echo 'NO INSTALADO ❌')"
echo "- uv: $(uv --version || echo 'NO INSTALADO ❌')"

echo
echo "🎉 Setup completado."
echo "➡ Ahora levantá el entorno con:"
echo "   cd $BASE/infra && docker compose up -d"
echo
echo "➡ Para crear el proyecto Django dentro de app:"
echo "   cd $BASE/app"
echo "   uv sync"
echo "   uv run django-admin startproject lucy ."
echo "   uv run python manage.py migrate"
echo "   uv run python manage.py runserver 0.0.0.0:8000"
echo
echo "📌 Servicios:"
echo " - Postgres: localhost:5432"
echo " - pgweb:    http://localhost:8081"
echo " - Mock API: http://localhost:8090"

