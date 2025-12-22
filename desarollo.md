  🔧 Despliegue para DESARROLLO (Local)

  Para trabajar en desarrollo local con hot-reload:

# 1. Activar el entorno virtual (si lo necesitas para instalar/actualizar dependencias)

  source .venv/bin/activate

# 2. Levantar los servicios con Docker

  ./dev.sh

# O manualmente:

  docker compose -f docker-compose.dev.yml up

  Servicios disponibles en desarrollo:

- Django admin: http://localhost:8000/admin

- MailHog (emails): http://localhost:8025

- PgAdmin: http://localhost:5050

- PostgreSQL: localhost:5432

- Redis: localhost:6379
  
  Características del entorno dev:

- Hot-reload automático (los cambios en ./src se ven inmediatamente)

- DEBUG=True

- MailHog captura todos los emails

- Credenciales de Teams/Moodle de testing

  ---

  🚀 Despliegue a TESTING (Servidor)

  Para subir cambios al servidor de testing:

# En el servidor de testing, ejecuta:

  ./update-testing-prod.sh testing

  Este script hace automáticamente:

1. git pull origin main - Baja últimos cambios

2. Aplica migraciones pendientes

3. Reinicia servicios (web, celery, celery-beat)

4. Verifica estado y muestra logs
   
   Acceso al servidor testing:
- Django: http://IP_SERVIDOR:8000
- MailHog: http://IP_SERVIDOR:8025
- PgAdmin: http://IP_SERVIDOR:5050

  ---

  📋 Flujo de trabajo típico

  Desarrollo local:

# 1. Hacer cambios en el código

# 2. Probar localmente

  ./dev.sh

# 3. Si hiciste cambios en modelos, crear migraciones

  docker compose -f docker-compose.dev.yml exec web python manage.py makemigrations

# 4. Aplicar migraciones localmente

  docker compose -f docker-compose.dev.yml exec web python manage.py migrate

# 5. Commit y push

  git add .
  git commit -m "feat: descripción del cambio"
  git push origin main

  Subir a testing:

# En el servidor de testing:

  ./update-testing-prod.sh testing

  ---

  ⚙️ Comandos útiles

# Ver logs en tiempo real

  ./comandos-comunes.sh logs testing    # (en testing)
  docker compose -f docker-compose.dev.yml logs -f web  # (en dev)

# Ver estado de servicios

  docker compose -f docker-compose.dev.yml ps

# Django shell

  docker compose -f docker-compose.dev.yml exec web python manage.py shell

# Crear superusuario

  docker compose -f docker-compose.dev.yml exec web python manage.py createsuperuser

# Detener servicios

