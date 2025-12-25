# Configuración de Variables de Entorno - PyLucy

Este documento explica cómo usar los archivos de configuración de entorno.

## 📁 Archivos Disponibles

- **`env-testing.txt`** - Configuración para servidor de testing/desarrollo
- **`env-production.txt`** - Configuración para servidor de producción

## 🚀 Uso Rápido

### Para Testing/Desarrollo

```bash
# 1. Copiar archivo de configuración
cp env-testing.txt .env.dev

# 2. Levantar servicios
docker compose -f docker-compose.testing.yml up -d

# 3. Acceder al sistema
# - Admin Django: http://localhost:8000/admin
# - MailHog (emails): http://localhost:8025
# - PgAdmin (BD): http://localhost:5050
```

### Para Producción

```bash
# 1. Copiar archivo de configuración
cp env-production.txt .env.prod

# 2. IMPORTANTE: Editar .env.prod y cambiar:
#    - SECRET_KEY (generar una nueva)
#    - DB_PASSWORD (contraseña segura)
#    - EMAIL_HOST_PASSWORD (credenciales SMTP)
#    - ALLOWED_HOSTS (dominio real del servidor)
nano .env.prod

# 3. Generar SECRET_KEY (copiar y pegar en .env.prod)
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# 4. Levantar servicios
docker compose -f docker-compose.prod.yml up -d
```

## 🔑 Diferencias Clave entre Testing y Producción

| Aspecto | Testing | Producción |
|---------|---------|------------|
| **Prefijo de cuentas** | `test-a` | `a` |
| **Ejemplo email Teams** | test-a12345678@eco.unrc.edu.ar | a12345678@eco.unrc.edu.ar |
| **DEBUG** | True | False |
| **Emails** | MailHog (captura) | SMTP real (envía) |
| **API UTI** | Mock (opcional) | Real |
| **Base de datos** | pylucy (testing) | pylucy (producción) |
| **Logs** | DEBUG (verbose) | INFO (importante) |

## ⚙️ Variables de Entorno Importantes

### Django

- `DJANGO_DEBUG`: True/False - Modo debug (NUNCA True en producción)
- `SECRET_KEY`: Clave secreta única de Django
- `ALLOWED_HOSTS`: Dominios permitidos (separados por comas)
- `ENVIRONMENT_MODE`: testing/production
- `ACCOUNT_PREFIX`: test-a (testing) / a (producción)

### Base de Datos

- `DB_NAME`: Nombre de la base de datos
- `DB_USER`: Usuario PostgreSQL
- `DB_PASSWORD`: Contraseña PostgreSQL
- `DB_HOST`: Host de la base de datos (normalmente "db")
- `DB_PORT`: Puerto PostgreSQL (5432)

### SIAL/UTI API

- `SIAL_BASE_URL`: URL de la API (mock o real)
- `SIAL_BASIC_USER`: Usuario para autenticación básica
- `SIAL_BASIC_PASS`: Contraseña para autenticación básica

### Moodle

- `MOODLE_BASE_URL`: URL del servidor Moodle
- `MOODLE_WSTOKEN`: Token de webservices de Moodle

### Email (SMTP)

- `EMAIL_HOST`: Servidor SMTP
- `EMAIL_PORT`: Puerto SMTP (587 o 25)
- `EMAIL_USE_TLS`: True/False
- `EMAIL_HOST_USER`: Usuario del correo
- `EMAIL_HOST_PASSWORD`: Contraseña del correo
- `DEFAULT_FROM_EMAIL`: Email remitente

### Microsoft Teams / Azure AD

- `TEAMS_TENANT`: GUID del tenant de Azure AD
- `TEAMS_DOMAIN`: Dominio de Teams (eco.unrc.edu.ar)
- `TEAMS_CLIENT_ID`: Application (client) ID
- `TEAMS_CLIENT_SECRET`: Client secret

### Celery / Redis

- `CELERY_BROKER_URL`: URL del broker Redis
- `CELERY_RESULT_BACKEND`: URL del backend de resultados

## 🔧 Comandos Útiles

### Generar SECRET_KEY para Producción

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### Ver logs en tiempo real

```bash
# Testing
docker compose -f docker-compose.testing.yml logs -f web

# Producción
docker compose -f docker-compose.prod.yml logs -f web
```

### Backup de Base de Datos

```bash
# Testing
docker compose -f docker-compose.testing.yml exec db pg_dump -U pylucy pylucy > backup_testing_$(date +%Y%m%d_%H%M%S).sql

# Producción
docker compose -f docker-compose.prod.yml exec db pg_dump -U pylucy pylucy > backup_prod_$(date +%Y%m%d_%H%M%S).sql
```

### Restaurar Base de Datos

```bash
# Testing
docker compose -f docker-compose.testing.yml exec -T db psql -U pylucy pylucy < backup.sql

# Producción
docker compose -f docker-compose.prod.yml exec -T db psql -U pylucy pylucy < backup.sql
```

### Ejecutar migraciones

```bash
# Testing
docker compose -f docker-compose.testing.yml exec web python manage.py migrate

# Producción
docker compose -f docker-compose.prod.yml exec web python manage.py migrate
```

### Crear superusuario

```bash
# Testing
docker compose -f docker-compose.testing.yml exec web python manage.py createsuperuser

# Producción
docker compose -f docker-compose.prod.yml exec web python manage.py createsuperuser
```

## 🔒 Seguridad

### Importante para Producción

1. **Nunca usar DEBUG=True** en producción
2. **Cambiar todas las contraseñas** por defecto
3. **Generar SECRET_KEY única** para cada entorno
4. **Configurar HTTPS** y activar las variables de seguridad
5. **Limitar ALLOWED_HOSTS** solo a dominios reales
6. **Hacer backups regulares** de la base de datos
7. **Revisar logs** periódicamente

### Variables de Seguridad HTTPS (descomentar en producción con SSL)

```bash
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True
```

## 📊 Monitoreo

### Verificar estado de servicios

```bash
# Testing
docker compose -f docker-compose.testing.yml ps

# Producción
docker compose -f docker-compose.prod.yml ps
```

### Verificar salud de la base de datos

```bash
# Testing
docker compose -f docker-compose.testing.yml exec db pg_isready -U pylucy

# Producción
docker compose -f docker-compose.prod.yml exec db pg_isready -U pylucy
```

### Ver uso de recursos

```bash
docker stats
```

## 🆘 Solución de Problemas

### Error: "required variable DB_PASSWORD is missing"

```bash
# Verificar que existe el archivo .env
ls -la .env.dev    # para testing
ls -la .env.prod   # para producción

# Si no existe, copiar desde el template
cp env-testing.txt .env.dev
# o
cp env-production.txt .env.prod
```

### Error: "migrations not applied"

```bash
# Aplicar migraciones
docker compose -f docker-compose.testing.yml exec web python manage.py migrate
```

### Error: "connection refused" a la base de datos

```bash
# Verificar que el contenedor de BD está corriendo
docker compose -f docker-compose.testing.yml ps db

# Ver logs de la base de datos
docker compose -f docker-compose.testing.yml logs db
```

## 📝 Notas Adicionales

- Los archivos `env-testing.txt` y `env-production.txt` están en el repositorio porque es **privado**
- El archivo `.env.dev` y `.env.prod` están en `.gitignore` para evitar commits accidentales
- Siempre usar `cp` para copiar los templates, nunca mover los originales
- Las credenciales de testing son compartidas, las de producción deben ser únicas y seguras
