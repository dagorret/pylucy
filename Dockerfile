# Imagen base: Python 3.12 slim
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Dependencias del sistema para Postgres y compilación
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Instalar dependencias de Python
COPY requirements.txt /app/

RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copiar código de la app para producción.
# En desarrollo se va a montar ./src sobre /app y esto se "pisa".
COPY src/ /app/

EXPOSE 8000
# El comando lo define docker-compose (runserver en dev, gunicorn en prod)

