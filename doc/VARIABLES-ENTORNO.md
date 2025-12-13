# Variables de Entorno - Desarrollo vs Producción

## 🎯 Referencia Rápida

**Tag**: `#ETME` (Environment Testing Mode)

---

## 📋 Tabla Comparativa Completa

| Variable               | Desarrollo (Testing)               | Producción                                          |
| ---------------------- | ---------------------------------- | --------------------------------------------------- |
| **ENVIRONMENT_MODE**   | `testing`                          | `production`                                        |
| **DJANGO_DEBUG**       | `True`                             | `False`                                             |
| **DJANGO_ENV**         | `development`                      | `production`                                        |
| **ALLOWED_HOSTS**      | `*`                                | `v.eco.unrc.edu.ar`                                 |
|                        |                                    |                                                     |
| **🔐 Base de Datos**   |                                    |                                                     |
| DB_ENGINE              | `django.db.backends.postgresql`    | `django.db.backends.postgresql`                     |
| DB_NAME                | `pylucy`                           | `pylucy_prod`                                       |
| DB_USER                | `pylucy`                           | `pylucy_prod`                                       |
| DB_PASSWORD            | `pylucy`                           | `[SECRETO]`                                         |
| DB_HOST                | `db` (Docker)                      | `db` (Docker) o IP servidor                         |
| DB_PORT                | `5432`                             | `5432`                                              |
|                        |                                    |                                                     |
| **📧 Email**           |                                    |                                                     |
| EMAIL_HOST             | `mailhog`                          | `smtp.eco.unrc.edu.ar`                              |
| EMAIL_PORT             | `1025`                             | `587`                                               |
| EMAIL_HOST_USER        | *(vacío)*                          | `noreply@eco.unrc.edu.ar`                           |
| EMAIL_HOST_PASSWORD    | *(vacío)*                          | `[SECRETO]`                                         |
| EMAIL_USE_TLS          | `False`                            | `True`                                              |
|                        |                                    |                                                     |
| **🎓 Moodle**          |                                    |                                                     |
| MOODLE_BASE_URL        | `https://sandbox.moodledemo.net`   | `https://moodle.eco.unrc.edu.ar`                    |
| MOODLE_WSTOKEN         | *(vacío o token sandbox)*          | `[SECRETO]`                                         |
|                        |                                    |                                                     |
| **👥 Microsoft Teams** |                                    |                                                     |
| TEAMS_TENANT           | `eco.unrc.edu.ar`                  | `eco.unrc.edu.ar`                                   |
| TEAMS_CLIENT_ID        | *(testing app)*                    | `[SECRETO]`                                         |
| TEAMS_CLIENT_SECRET    | *(testing app)*                    | `[SECRETO]`                                         |
|                        |                                    |                                                     |
| **🔧 SIAL/UTI Mock**   |                                    |                                                     |
| SIAL_BASE_URL          | `http://host.docker.internal:8088` | `https://api.sial.unrc.edu.ar` (si existe API real) |
| SIAL_BASIC_USER        | `usuario`                          | `[SECRETO]`                                         |
| SIAL_BASIC_PASS        | `contrasena`                       | `[SECRETO]`                                         |

---

## 📄 Archivo: `docker-compose.dev.yml`

```yaml
version: "3.9"

services:
  web:
    build: .
    container_name: pylucy-web-dev
    command: python manage.py runserver 0.0.0.0:8000
    volumes:
      - ./src:/app
    extra_hosts:
      - "host.docker.internal:host-gateway"
    ports:
      - "8000:8000"
    environment:
      # Django
      - DJANGO_DEBUG=True
      - DJANGO_ENV=development

      # #ETME - Modo testing
      - ENVIRONMENT_MODE=testing

      # SIAL/UTI Mock
      - SIAL_BASE_URL=http://host.docker.internal:8088
      - SIAL_BASIC_USER=usuario
      - SIAL_BASIC_PASS=contrasena

      # Database
      - DB_ENGINE=django.db.backends.postgresql
      - DB_NAME=pylucy
      - DB_USER=pylucy
      - DB_PASSWORD=pylucy
      - DB_HOST=db
      - DB_PORT=5432

      # Email (MailHog)
      - EMAIL_HOST=mailhog
      - EMAIL_PORT=1025

      # Moodle (Sandbox)
      - MOODLE_BASE_URL=https://sandbox.moodledemo.net
      - MOODLE_WSTOKEN=

      # Microsoft Teams (Testing App)
      - TEAMS_TENANT=eco.unrc.edu.ar
      - TEAMS_CLIENT_ID=
      - TEAMS_CLIENT_SECRET=

    depends_on:
      - db
    networks:
      - pylucy-net

  db:
    image: postgres:16
    container_name: pylucy-db-dev
    restart: always
    environment:
      - POSTGRES_DB=pylucy
      - POSTGRES_USER=pylucy
      - POSTGRES_PASSWORD=pylucy
    ports:
      - "5432:5432"
    volumes:
      - pylucy-db-dev:/var/lib/postgresql/data
    networks:
      - pylucy-net

  pgadmin:
    image: dpage/pgadmin4
    container_name: pylucy-pgadmin-dev
    restart: always
    environment:
      - PGADMIN_DEFAULT_EMAIL=admin@unrc.edu.ar
      - PGADMIN_DEFAULT_PASSWORD=admin
    ports:
      - "5050:80"
    networks:
      - pylucy-net

  mailhog:
    image: mailhog/mailhog
    container_name: pylucy-mailhog-dev
    restart: always
    ports:
      - "8025:8025"   # UI Web
      - "1025:1025"   # SMTP
    networks:
      - pylucy-net

networks:
  pylucy-net:

volumes:
  pylucy-db-dev:
```

---

## 📄 Archivo: `docker-compose.prod.yml`

```yaml
version: "3.9"

services:
  web:
    build: .
    container_name: pylucy-web-prod
    command: gunicorn pylucy.wsgi:application --bind 0.0.0.0:8000 --workers 4
    volumes:
      - ./src:/app
      - ./staticfiles:/app/staticfiles
    ports:
      - "8000:8000"
    environment:
      # Django
      - DJANGO_DEBUG=False
      - DJANGO_ENV=production

      # #ETME - Modo producción
      - ENVIRONMENT_MODE=production

      # SIAL/UTI (API Real si existe)
      - SIAL_BASE_URL=${SIAL_BASE_URL}
      - SIAL_BASIC_USER=${SIAL_BASIC_USER}
      - SIAL_BASIC_PASS=${SIAL_BASIC_PASS}

      # Database
      - DB_ENGINE=django.db.backends.postgresql
      - DB_NAME=pylucy_prod
      - DB_USER=pylucy_prod
      - DB_PASSWORD=${DB_PASSWORD}
      - DB_HOST=db
      - DB_PORT=5432

      # Email (SMTP Real)
      - EMAIL_HOST=smtp.eco.unrc.edu.ar
      - EMAIL_PORT=587
      - EMAIL_HOST_USER=noreply@eco.unrc.edu.ar
      - EMAIL_HOST_PASSWORD=${EMAIL_PASSWORD}
      - EMAIL_USE_TLS=True

      # Moodle (Producción)
      - MOODLE_BASE_URL=https://moodle.eco.unrc.edu.ar
      - MOODLE_WSTOKEN=${MOODLE_PROD_TOKEN}

      # Microsoft Teams (Prod App)
      - TEAMS_TENANT=eco.unrc.edu.ar
      - TEAMS_CLIENT_ID=${TEAMS_PROD_CLIENT_ID}
      - TEAMS_CLIENT_SECRET=${TEAMS_PROD_CLIENT_SECRET}

      # Security
      - ALLOWED_HOSTS=v.eco.unrc.edu.ar,localhost

    depends_on:
      - db
    networks:
      - pylucy-net

  db:
    image: postgres:16
    container_name: pylucy-db-prod
    restart: always
    environment:
      - POSTGRES_DB=pylucy_prod
      - POSTGRES_USER=pylucy_prod
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - pylucy-db-prod:/var/lib/postgresql/data
    networks:
      - pylucy-net

  nginx:
    image: nginx:alpine
    container_name: pylucy-nginx-prod
    restart: always
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./staticfiles:/staticfiles:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - web
    networks:
      - pylucy-net

networks:
  pylucy-net:

volumes:
  pylucy-db-prod:
```

---

## 📄 Archivo: `.env.prod` (NO COMMITEAR)

```bash
# ============================================================
# ARCHIVO DE SECRETOS PARA PRODUCCIÓN
# ============================================================
# IMPORTANTE: Este archivo NO debe ir al repositorio
# Debe estar en .gitignore
# ============================================================

# Modo de ejecución
ENVIRONMENT_MODE=production

# Base de datos
DB_PASSWORD=contraseña_super_segura_aqui

# Email SMTP
EMAIL_PASSWORD=contraseña_smtp_real

# Moodle Producción
MOODLE_PROD_TOKEN=token_obtenido_desde_moodle_admin

# Microsoft Teams (App Registration de Producción)
TEAMS_PROD_CLIENT_ID=12345678-1234-1234-1234-123456789abc
TEAMS_PROD_CLIENT_SECRET=secreto_muy_largo_de_azure_ad

# SIAL/UTI (si hay API real)
SIAL_BASE_URL=https://api.sial.unrc.edu.ar
SIAL_BASIC_USER=usuario_produccion
SIAL_BASIC_PASS=contraseña_produccion
```

---

## 🚀 Comandos para Ejecutar

### Desarrollo (Testing)

```bash
# Levantar servicios
docker compose -f docker-compose.dev.yml up -d

# Ver logs
docker compose -f docker-compose.dev.yml logs -f web

# Verificar modo
docker exec pylucy-web-dev python manage.py check_environment

# Accesos:
# - Django Admin: http://localhost:8000/admin
# - MailHog UI: http://localhost:8025
# - PgAdmin: http://localhost:5050
# - Mock API UTI: http://localhost:8088
```

### Producción

```bash
# Cargar variables de entorno
export $(cat .env.prod | xargs)

# O usar --env-file
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d

# Ver logs
docker compose -f docker-compose.prod.yml logs -f web

# Verificar modo (CRÍTICO)
docker exec pylucy-web-prod python manage.py check_environment

# Ejecutar migraciones
docker exec pylucy-web-prod python manage.py migrate

# Recolectar estáticos
docker exec pylucy-web-prod python manage.py collectstatic --noinput

# Crear superusuario
docker exec -it pylucy-web-prod python manage.py createsuperuser
```

---

## ⚠️ CHECKLIST Pre-Producción

Antes de ejecutar en producción, verificar:

- [ ] `ENVIRONMENT_MODE=production` configurado
- [ ] Archivo `.env.prod` creado con todos los secretos
- [ ] `.env.prod` está en `.gitignore`
- [ ] `DJANGO_DEBUG=False`
- [ ] Credenciales de BD de producción configuradas
- [ ] Token de Moodle de producción obtenido
- [ ] App Registration de Teams de producción configurada
- [ ] SMTP real configurado (smtp.eco.unrc.edu.ar)
- [ ] `ALLOWED_HOSTS` configurado correctamente
- [ ] SSL/TLS configurado en nginx
- [ ] Ejecutar `check_environment` para confirmar modo
- [ ] Hacer backup de BD antes de migrar
- [ ] Probar en staging antes de producción

---

## 🔍 Verificar Configuración Actual

```bash
# Ver modo actual
docker exec pylucy-web-dev python manage.py check_environment

# Resultado esperado en DESARROLLO:
# ============================================================
# MODO ACTUAL: TESTING
# ============================================================
# Prefix: test-a
# Example: test-a12345678@eco.unrc.edu.ar
# Moodle: https://sandbox.moodledemo.net
# Email: mailhog:1025

# Resultado esperado en PRODUCCIÓN:
# ============================================================
# MODO ACTUAL: PRODUCTION
# ============================================================
# Prefix: a
# Example: a12345678@eco.unrc.edu.ar
# Moodle: https://moodle.eco.unrc.edu.ar
# Email: smtp.eco.unrc.edu.ar:587
```

---

## 📊 Resumen de Diferencias Clave

| Aspecto         | Desarrollo                | Producción       |
| --------------- | ------------------------- | ---------------- |
| **Prefijo UPN** | `test-a`                  | `a`              |
| **Debug**       | ✅ Activo                  | ❌ Desactivado    |
| **Email**       | MailHog (fake)            | SMTP Real        |
| **Moodle**      | Sandbox (reset cada hora) | Producción       |
| **Teams**       | App Testing               | App Producción   |
| **Secretos**    | Hardcoded                 | `.env.prod`      |
| **Datos**       | Temporal/Testing          | Persistente/Real |

---

## 🔐 Seguridad

### Archivos que NO deben ir al repositorio:

```
.env.prod
.env.production
.env.secrets
*.env (excepto .env.example)
```

### Verificar .gitignore:

```bash
# Ver si .env.prod está ignorado
git check-ignore .env.prod

# Resultado esperado:
# .env.prod
```

---

## 📚 Documentos Relacionados

- `TESTING-VS-PRODUCCION.md` - Detalles técnicos de implementación
- `estrategia-testing-integracion.md` - Estrategia de testing con servicios reales
- Ver tag `#ETME` en código para ubicar cambios

---

**Última actualización**: 2025-12-08
**Autor**: Sistema Lucy AMS
