# Guía de Deployment - PyLucy Testing

Esta guía describe cómo desplegar PyLucy en el servidor de testing usando Docker.

## Requisitos Previos

En el servidor de testing necesitas tener instalado:
- Docker (20.10+)
- Docker Compose (2.0+)
- Git

### Verificar instalación de Docker

```bash
docker --version
docker compose version
```

## Opción 1: Deployment con HTTPS (Recomendado)

### Paso 1: Conectarse al servidor de testing

```bash
ssh usuario@servidor-testing.unrc.edu.ar
```

### Paso 2: Clonar el repositorio

```bash
# Navegar al directorio deseado
cd /opt  # o el directorio que prefieras

# Clonar usando HTTPS
git clone https://github.com/tu-usuario/pylucy.git
cd pylucy
```

### Paso 3: Configuración inicial

```bash
# Ejecutar setup para crear .env.prod
./deploy.sh setup
```

Este comando:
- Crea el archivo `.env.prod` desde `.env.prod.example`
- Genera automáticamente el `SECRET_KEY` de Django
- Te indicará qué variables debes configurar

### Paso 4: Editar configuración de producción

Edita el archivo `.env.prod` con los valores del entorno de testing:

```bash
nano .env.prod
```

Variables importantes a configurar:

```bash
# Django
ALLOWED_HOSTS=servidor-testing.unrc.edu.ar,IP_DEL_SERVIDOR

# Base de datos (cambiar contraseña)
DB_PASSWORD=UNA_CONTRASEÑA_SEGURA_POSTGRESQL

# SIAL/UTI API
SIAL_BASE_URL=https://sial.unrc.edu.ar
SIAL_BASIC_USER=usuario_sial
SIAL_BASIC_PASS=contraseña_sial

# Moodle
MOODLE_BASE_URL=https://moodle.eco.unrc.edu.ar
MOODLE_WSTOKEN=token_de_moodle

# Email SMTP
EMAIL_HOST=smtp.eco.unrc.edu.ar
EMAIL_HOST_USER=no-reply@eco.unrc.edu.ar
EMAIL_HOST_PASSWORD=contraseña_smtp

# Microsoft Teams (usar credenciales de testing)
TEAMS_TENANT=1f7d4699-ccd7-45d6-bc78-b8b950bcaedc
TEAMS_CLIENT_ID=138e98af-33e5-439c-9981-3caaedc65c70
TEAMS_CLIENT_SECRET=VE~8Q~SbnnIUg-iEHnr1m8nxu5J0RAskpLJPlbuU

# Modo de ambiente
ENVIRONMENT_MODE=testing  # Usa prefijo "test-a" para cuentas
```

### Paso 5: Iniciar los servicios

```bash
./deploy.sh start
```

Este comando:
1. Construye las imágenes Docker
2. Inicia todos los servicios (web, db, redis, celery, nginx)
3. Ejecuta las migraciones automáticamente
4. Recolecta archivos estáticos

### Paso 6: Verificar el estado

```bash
./deploy.sh status
```

### Paso 7: Crear superusuario de Django

```bash
docker compose -f docker-compose.prod.yml exec web python manage.py createsuperuser
```

### Paso 8: Acceder a la aplicación

Abre tu navegador en:
- Aplicación: `http://servidor-testing.unrc.edu.ar`
- Admin: `http://servidor-testing.unrc.edu.ar/admin`

## Comandos del Script de Deployment

El script `deploy.sh` facilita las operaciones comunes:

```bash
# Ver ayuda
./deploy.sh help

# Primera instalación
./deploy.sh setup

# Iniciar servicios
./deploy.sh start

# Detener servicios
./deploy.sh stop

# Reiniciar servicios
./deploy.sh restart

# Ver logs en tiempo real
./deploy.sh logs

# Ver estado de los servicios
./deploy.sh status

# Actualizar código y rebuild
./deploy.sh update

# Crear backup de la base de datos
./deploy.sh backup

# Abrir shell en el contenedor web
./deploy.sh shell

# Abrir shell de PostgreSQL
./deploy.sh dbshell

# Limpiar todo (¡CUIDADO! Elimina datos)
./deploy.sh clean
```

## Actualización del Sistema

Cuando haya cambios en el código:

```bash
# Desde el servidor
cd /opt/pylucy

# Opción 1: Actualización automática
./deploy.sh update

# Opción 2: Actualización manual
git pull
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml up -d
docker compose -f docker-compose.prod.yml exec web python manage.py migrate
docker compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput
```

## Backup y Restauración

### Crear backup

```bash
# Usando el script
./deploy.sh backup

# Manual
docker compose -f docker-compose.prod.yml exec -T db pg_dump -U pylucy pylucy > backup_$(date +%Y%m%d_%H%M%S).sql
```

### Restaurar backup

```bash
# Detener servicios
./deploy.sh stop

# Restaurar
docker compose -f docker-compose.prod.yml up -d db
cat backup_FECHA.sql | docker compose -f docker-compose.prod.yml exec -T db psql -U pylucy -d pylucy

# Reiniciar todos los servicios
./deploy.sh start
```

## Monitoreo y Logs

### Ver logs de todos los servicios

```bash
./deploy.sh logs
```

### Ver logs de un servicio específico

```bash
docker compose -f docker-compose.prod.yml logs -f web
docker compose -f docker-compose.prod.yml logs -f celery
docker compose -f docker-compose.prod.yml logs -f db
docker compose -f docker-compose.prod.yml logs -f nginx
```

### Ver logs de Django en el contenedor

```bash
docker compose -f docker-compose.prod.yml exec web tail -f /app/logs/django.log
```

## Arquitectura de Servicios

El deployment incluye los siguientes servicios:

- **nginx**: Servidor web (puerto 80)
  - Sirve archivos estáticos
  - Proxy reverso a Django
  - Balanceo de carga

- **web**: Aplicación Django con Gunicorn
  - 4 workers
  - Timeout de 120s

- **db**: PostgreSQL 16
  - Datos persistentes en volumen `pylucy-db-prod`

- **redis**: Redis 7
  - Broker para Celery
  - Datos persistentes en volumen `pylucy-redis-prod`

- **celery**: Worker para tareas asíncronas
  - 4 procesos concurrentes

- **celery-beat**: Scheduler para tareas periódicas
  - Programación basada en base de datos

## Solución de Problemas

### Los servicios no inician

```bash
# Ver logs de error
docker compose -f docker-compose.prod.yml logs

# Verificar que .env.prod esté configurado
cat .env.prod

# Verificar que Docker tenga suficiente memoria
docker system df
```

### Error de migraciones

```bash
# Ejecutar migraciones manualmente
docker compose -f docker-compose.prod.yml exec web python manage.py migrate
```

### Error 502 Bad Gateway

```bash
# Verificar que el servicio web esté corriendo
docker compose -f docker-compose.prod.yml ps web

# Ver logs del servicio web
docker compose -f docker-compose.prod.yml logs web

# Verificar healthcheck
docker compose -f docker-compose.prod.yml exec web curl -f http://localhost:8000/admin/login/
```

### Archivos estáticos no se cargan

```bash
# Recolectar archivos estáticos
docker compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput

# Verificar volumen de nginx
docker compose -f docker-compose.prod.yml exec nginx ls -la /app/staticfiles/
```

### Celery no procesa tareas

```bash
# Ver logs de celery
docker compose -f docker-compose.prod.yml logs celery

# Verificar conexión a Redis
docker compose -f docker-compose.prod.yml exec celery celery -A pylucy inspect ping

# Ver tareas activas
docker compose -f docker-compose.prod.yml exec celery celery -A pylucy inspect active
```

## Seguridad

### Cambiar contraseñas

Después del primer deployment, considera cambiar:

1. Contraseña de PostgreSQL
2. Contraseña del superusuario de Django
3. SECRET_KEY de Django (ya se genera automáticamente)

### Firewall

Asegúrate de que el firewall del servidor solo permita:
- Puerto 80 (HTTP)
- Puerto 443 (HTTPS cuando esté configurado)
- Puerto 22 (SSH)

```bash
# Ejemplo con ufw
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 22/tcp
sudo ufw enable
```

## Opción 2: Deployment con SSH (Alternativa)

Si prefieres usar SSH en lugar de HTTPS:

### Paso 1: Generar claves SSH (en tu máquina local)

```bash
# Si no tienes claves SSH
ssh-keygen -t ed25519 -C "tu-email@unrc.edu.ar"
```

### Paso 2: Agregar clave pública a GitHub

```bash
# Copiar clave pública
cat ~/.ssh/id_ed25519.pub
```

Ve a GitHub → Settings → SSH and GPG keys → New SSH key

### Paso 3: Clonar con SSH

```bash
# En el servidor
git clone git@github.com:tu-usuario/pylucy.git
cd pylucy
```

Luego sigue los pasos desde el Paso 3 de la Opción 1.

## Próximos Pasos

Una vez que el sistema esté funcionando en testing:

1. Configurar SSL/HTTPS con Let's Encrypt
2. Configurar backups automáticos
3. Configurar monitoreo (Prometheus, Grafana)
4. Configurar alertas
5. Documentar procedimientos de emergencia

## Configuración de SSL/HTTPS (Futuro)

Cuando estés listo para HTTPS:

1. Obtener certificado SSL (Let's Encrypt con Certbot)
2. Descomentar puerto 443 en `docker-compose.prod.yml`
3. Actualizar configuración de nginx para SSL
4. Habilitar redirección HTTP → HTTPS
5. Actualizar variables en `.env.prod`:
   ```
   SECURE_SSL_REDIRECT=True
   SESSION_COOKIE_SECURE=True
   CSRF_COOKIE_SECURE=True
   ```

## Contacto y Soporte

Para problemas o preguntas:
- Revisar logs: `./deploy.sh logs`
- Verificar estado: `./deploy.sh status`
- Crear issue en GitHub
