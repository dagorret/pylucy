# pylucy

Entorno de desarrollo para el proyecto *Lucy* usando **Django**, **PostgreSQL** y una **API mock** de la UTI.

## Estructura del proyecto

```text
pylucy/
  infra/          # Docker Compose: Postgres, pgweb, API mock UTI
  app/            # Proyecto Django (código de la aplicación)
  ops/            # Makefile y scripts de automatización
  docs/           # Documentación
  mock-api-uti/   # Clon de https://github.com/dagorret/api-mock-lucy
```

## Requisitos

- Docker y docker compose
- Python 3.12
- [uv](https://github.com/astral-sh/uv)
- git

## Primer uso

1. Clonar el repositorio:

```bash
git clone git@github.com:dagorret/pylucy.git
cd pylucy
```

2. Levantar la infraestructura (Postgres, pgweb, API mock):

```bash
cd infra
docker compose up -d
```

Servicios:

- Postgres: `localhost:5432` (DB: `appdb`, usuario: `app`, pass: `app`)
- pgweb: `http://localhost:8081`
- API mock UTI: `http://localhost:8090`

3. Preparar el entorno Django:

```bash
cd ../app
uv sync
uv run django-admin startproject lucy .
uv run python manage.py migrate
uv run python manage.py createsuperuser
uv run python manage.py runserver 0.0.0.0:8000
```

Panel de administración:

- `http://localhost:8000/admin`

## Notas

- La API mock de la UTI se encuentra en `mock-api-uti/` y se expone en el puerto `8090`.
- La base de datos PostgreSQL se define en `infra/docker-compose.yml` y la aplicación Django se conecta a través de las variables de entorno en `app/.env`.
- Para desarrollo, se recomienda usar `uv` localmente y dejar los servicios externos (Postgres, pgweb, mock API) dentro de Docker.

